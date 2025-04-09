import logging
import aiomysql
import asyncio
import os
import json
from mysql.connector import Error
from typing import List, Dict, Any, Optional
from .config import settings
from .security.password import hash_password

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

class Database:
    def __init__(self):
        self.pool = None
        self.connected = False
        self.max_retries = 5
        self.retry_delay = 1  # seconds
        self.use_external_db = False
        self.ext_db_config = {}
        self.local_pool = None  # For maintaining a connection to local DB even when using external

    async def connect(self):
        """
        Connect to the database with retry logic
        """
        # Check if external database config exists and should be used
        try:
            self.use_external_db = settings.use_external_db
            if self.use_external_db and settings.external_db_config:
                self.ext_db_config = json.loads(settings.external_db_config)
                logger.info("Using external database configuration")
        except Exception as e:
            logger.warning(f"Error loading external database config: {e}")
            self.use_external_db = False
        
        # Always connect to the local database for user authentication
        await self._connect_to_local_db()
        
        # If using external DB, also connect to it
        if self.use_external_db:
            await self._connect_to_external_db()
        
    async def _connect_to_local_db(self):
        """Connect to the local database"""
        retries = 0
        while retries < self.max_retries:
            try:
                self.local_pool = await aiomysql.create_pool(
                    host=settings.db_host,
                    user=settings.db_user,
                    password=settings.db_password,
                    db=settings.db_database,
                    autocommit=True,
                    pool_recycle=3600,  # Recycle connections after 1 hour
                    maxsize=10,  # Maximum number of connections in the pool
                    minsize=1    # Minimum number of connections in the pool
                )
                
                if not self.use_external_db:
                    self.pool = self.local_pool
                logger.info("Successfully connected to local MySQL database")
                async with self.local_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT 1")
                        result = await cursor.fetchone()
                        logger.info(f"Database connection test: {result}")
                if not self.use_external_db:
                    self.connected = True
                return True
            except Exception as e:
                retries += 1
                logger.error(f"Error connecting to local MySQL database (attempt {retries}/{self.max_retries}): {e}")
                if retries >= self.max_retries:
                    logger.critical("Failed to connect to local database after maximum retries")
                    # Raise exception in production, but allow app to continue in development
                    if not settings.debug:
                        raise DatabaseError(f"Failed to connect to local database: {e}")
                    return False
                else:
                    # Wait before retrying with exponential backoff
                    await asyncio.sleep(self.retry_delay * (2 ** (retries - 1)))
                    
    async def _connect_to_external_db(self):
        """Connect to the external database"""
        if not self.ext_db_config:
            logger.error("External database configuration is empty")
            return False
            
        retries = 0
        while retries < self.max_retries:
            try:
                self.pool = await aiomysql.create_pool(
                    host=self.ext_db_config.get('host'),
                    user=self.ext_db_config.get('user'),
                    password=self.ext_db_config.get('password'),
                    db=self.ext_db_config.get('database'),
                    autocommit=True,
                    pool_recycle=3600,
                    maxsize=10,
                    minsize=1
                )
                
                logger.info("Successfully connected to external MySQL database")
                
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT 1")
                        result = await cursor.fetchone()
                        logger.info(f"External database connection test: {result}")
                
                self.connected = True
                
                # Create required tables in the external database
                await self._sync_schema_to_external()
                
                return True
                
            except Exception as e:
                retries += 1
                logger.error(f"Error connecting to external MySQL database (attempt {retries}/{self.max_retries}): {e}")
                if retries >= self.max_retries:
                    logger.critical("Failed to connect to external database after maximum retries")
                    # Fall back to local database
                    self.use_external_db = False
                    self.pool = self.local_pool
                    self.connected = True
                    logger.info("Falling back to local database")
                    return False
                else:
                    # Wait before retrying with exponential backoff
                    await asyncio.sleep(self.retry_delay * (2 ** (retries - 1)))

    async def _sync_schema_to_external(self):
        """Create necessary tables in external DB if they don't exist"""
        try:
            # Create essential tables in external database
            await self.create_tables_in_current_pool()
            
            # Sync tables from migrations
            migrations_path = os.path.join(os.path.dirname(__file__), 'migrations')
            
            # Execute migrations in the external database
            service_tables_migration = os.path.join(migrations_path, 'create_service_tables.sql')
            data_sync_jobs_migration = os.path.join(migrations_path, 'add_data_sync_jobs_table.sql')
            call_features_migration = os.path.join(migrations_path, 'add_call_features_tables.sql')
            
            if os.path.exists(service_tables_migration):
                await self.execute_migration(service_tables_migration)
                
            if os.path.exists(data_sync_jobs_migration):
                await self.execute_migration(data_sync_jobs_migration)
                
            if os.path.exists(call_features_migration):
                await self.execute_migration(call_features_migration)
                
            logger.info("Successfully synced schema to external database")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing schema to external database: {e}")
            return False
            
    async def execute(self, query: str, params: Any = None, use_local: bool = False) -> List[Dict[str, Any]]:
        """
        Execute a query with retry logic
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            use_local: Force using local database (for user auth queries)
        """
        # Determine which pool to use
        target_pool = self.local_pool if (use_local or query.lower().startswith("select") and "users" in query.lower()) else self.pool
        
        if not self.connected or not target_pool:
            if settings.debug:
                logger.warning("Database not connected, cannot execute query")
                return []
            else:
                # In production, attempt to reconnect
                await self.connect()
                if not self.connected:
                    raise DatabaseError("Database connection failed, cannot execute query")
        
        # Always use local database for user-related queries
        if "users" in query.lower() and not use_local:
            logger.info("Using local database for user-related query")
            target_pool = self.local_pool
        
        retries = 0
        while retries < self.max_retries:
            try:
                async with target_pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute(query, params or ())
                        result = await cursor.fetchall()
                        
                        # If using external DB, also save to local DB for backup (except for user queries)
                        if target_pool != self.local_pool and not query.lower().startswith("select") and "users" not in query.lower():
                            try:
                                async with self.local_pool.acquire() as local_conn:
                                    async with local_conn.cursor() as local_cursor:
                                        await local_cursor.execute(query, params or ())
                            except Exception as local_e:
                                logger.warning(f"Failed to backup to local database: {local_e}")
                        
                        return result
            except Exception as e:
                retries += 1
                logger.error(f"Database execution error (attempt {retries}/{self.max_retries}): {e}")
                if retries >= self.max_retries:
                    if settings.debug:
                        logger.error(f"Query failed after maximum retries: {query}")
                        return []
                    else:
                        raise DatabaseError(f"Query execution failed: {e}")
                else:
                    # Wait before retrying with exponential backoff
                    await asyncio.sleep(self.retry_delay * (2 ** (retries - 1)))

    async def execute_transaction(self, queries: List[Dict[str, Any]], use_local: bool = False) -> bool:
        """
        Execute multiple queries in a transaction
        Each query dict should have 'query' and optionally 'params' keys
        
        Args:
            queries: List of query dictionaries
            use_local: Force using local database
        """
        # Determine if this is a user-related transaction
        is_user_transaction = any("users" in q.get('query', '').lower() for q in queries)
        
        # Determine which pool to use
        target_pool = self.local_pool if (use_local or is_user_transaction) else self.pool
        
        if not self.connected or not target_pool:
            if settings.debug:
                logger.warning("Database not connected, cannot execute transaction")
                return False
            else:
                await self.connect()
                if not self.connected:
                    raise DatabaseError("Database connection failed, cannot execute transaction")
        
        retries = 0
        while retries < self.max_retries:
            try:
                async with target_pool.acquire() as conn:
                    # Disable autocommit for transaction
                    await conn.begin()
                    async with conn.cursor() as cursor:
                        for query_dict in queries:
                            await cursor.execute(
                                query_dict['query'], 
                                query_dict.get('params', ())
                            )
                    await conn.commit()
                    
                    # If using external DB, also execute in local DB for backup (except for user transactions)
                    if target_pool != self.local_pool and not is_user_transaction:
                        try:
                            async with self.local_pool.acquire() as local_conn:
                                await local_conn.begin()
                                async with local_conn.cursor() as local_cursor:
                                    for query_dict in queries:
                                        await local_cursor.execute(
                                            query_dict['query'], 
                                            query_dict.get('params', ())
                                        )
                                await local_conn.commit()
                        except Exception as local_e:
                            logger.warning(f"Failed to backup transaction to local database: {local_e}")
                    
                    return True
            except Exception as e:
                retries += 1
                logger.error(f"Transaction error (attempt {retries}/{self.max_retries}): {e}")
                try:
                    await conn.rollback()
                except:
                    pass
                
                if retries >= self.max_retries:
                    if settings.debug:
                        logger.error("Transaction failed after maximum retries")
                        return False
                    else:
                        raise DatabaseError(f"Transaction execution failed: {e}")
                else:
                    # Wait before retrying with exponential backoff
                    await asyncio.sleep(self.retry_delay * (2 ** (retries - 1)))

    async def execute_migration(self, migration_file: str) -> bool:
        """
        Execute a SQL migration file
        """
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
            
        try:
            with open(migration_file, 'r') as f:
                sql_content = f.read()
                
            # Split SQL content by semicolons to get individual statements
            # Skip empty statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            # Execute each statement in a transaction
            queries = [{'query': stmt} for stmt in statements]
            
            if await self.execute_transaction(queries):
                logger.info(f"Migration successful: {migration_file}")
                return True
            else:
                logger.error(f"Migration failed: {migration_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing migration {migration_file}: {e}")
            return False

    async def close(self):
        """
        Close database connection pools
        """
        if self.pool and self.pool != self.local_pool:
            self.pool.close()
            await self.pool.wait_closed()
        
        if self.local_pool:
            self.local_pool.close()
            await self.local_pool.wait_closed()
            
        self.connected = False
        logger.info("Database connections closed")

    async def create_tables_in_current_pool(self):
        """
        Create initial database tables in the current pool (used for external DB setup)
        """
        if not self.pool:
            logger.warning("No active pool to create tables in")
            return False
        
        try:
            queries = [
                # Create calls table
                {
                    'query': """
                        CREATE TABLE IF NOT EXISTS calls (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            call_sid VARCHAR(255) NOT NULL,
                            from_number VARCHAR(20) NOT NULL,
                            to_number VARCHAR(20) NOT NULL,
                            direction ENUM('inbound', 'outbound') NOT NULL,
                            status VARCHAR(50) NOT NULL,
                            start_time DATETIME NOT NULL,
                            end_time DATETIME,
                            duration INT,
                            recording_url TEXT,
                            transcription TEXT,
                            cost DECIMAL(10, 4),
                            segments INT,
                            ultravox_cost DECIMAL(10, 4),
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                    """
                },
                # Create error_logs table
                {
                    'query': """
                        CREATE TABLE IF NOT EXISTS error_logs (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            timestamp TIMESTAMP NOT NULL,
                            path VARCHAR(255) NOT NULL,
                            method VARCHAR(10) NOT NULL,
                            error_type VARCHAR(100) NOT NULL,
                            error_message TEXT NOT NULL,
                            traceback TEXT,
                            headers TEXT,
                            client_ip VARCHAR(45)
                        )
                    """
                }
            ]
            
            # Execute all queries in a transaction
            if await self.execute_transaction(queries, use_local=self.pool == self.local_pool):
                logger.info("Database tables created successfully in current pool")
                return True
        except Exception as e:
            logger.error(f"Error creating tables in current pool: {e}")
            return False

    async def switch_to_external(self, enable: bool = True, config: Dict = None):
        """
        Switch between local and external database
        
        Args:
            enable: Whether to enable external database
            config: External database configuration
        
        Returns:
            Success status
        """
        if enable and not config:
            logger.error("Cannot enable external database without configuration")
            return False
            
        try:
            # Update settings
            settings.use_external_db = enable
            if config:
                settings.external_db_config = json.dumps(config)
            
            # Reconnect with new settings
            if enable:
                self.use_external_db = True
                self.ext_db_config = config
                success = await self._connect_to_external_db()
                if not success:
                    # Revert to local if connection failed
                    self.use_external_db = False
                    self.pool = self.local_pool
                    logger.warning("Failed to connect to external database, using local database")
                    return False
            else:
                # Switch back to local
                self.use_external_db = False
                if self.pool and self.pool != self.local_pool:
                    self.pool.close()
                    await self.pool.wait_closed()
                self.pool = self.local_pool
                
            logger.info(f"Successfully switched database to {'external' if enable else 'local'}")
            return True
            
        except Exception as e:
            logger.error(f"Error switching database: {e}")
            return False
            
    async def test_connection(self, config: Dict) -> Dict:
        """
        Test connection to a database with the given configuration
        
        Args:
            config: Database configuration with host, user, password, database
            
        Returns:
            Dict with success status and message
        """
        if not all(k in config for k in ['host', 'user', 'password', 'database']):
            return {
                "success": False,
                "message": "Missing required configuration parameters"
            }
            
        try:
            test_pool = await aiomysql.create_pool(
                host=config['host'],
                user=config['user'],
                password=config['password'],
                db=config['database'],
                autocommit=True,
                pool_recycle=3600,
                maxsize=1,
                minsize=1
            )
            
            async with test_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    
            test_pool.close()
            await test_pool.wait_closed()
            
            return {
                "success": True,
                "message": "Connection successful"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }

db = Database()

async def create_tables():
    """
    Create initial database tables
    """
    # Skip table creation if database is not connected
    if not db.connected:
        await db.connect()
        if not db.connected:
            logger.warning("Database not connected, skipping table creation")
            return
        
    try:
        queries = [
            # Create users table
            {
                'query': """
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        is_admin BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """
            },
            # Create error_logs table
            {
                'query': """
                    CREATE TABLE IF NOT EXISTS error_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        path VARCHAR(255) NOT NULL,
                        method VARCHAR(10) NOT NULL,
                        error_type VARCHAR(100) NOT NULL,
                        error_message TEXT NOT NULL,
                        traceback TEXT,
                        headers TEXT,
                        client_ip VARCHAR(45)
                    )
                """
            },
            # Create calls table
            {
                'query': """
                    CREATE TABLE IF NOT EXISTS calls (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        call_sid VARCHAR(255) NOT NULL,
                        from_number VARCHAR(20) NOT NULL,
                        to_number VARCHAR(20) NOT NULL,
                        direction ENUM('inbound', 'outbound') NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        start_time DATETIME NOT NULL,
                        end_time DATETIME,
                        duration INT,
                        recording_url TEXT,
                        transcription TEXT,
                        cost DECIMAL(10, 4),
                        segments INT,
                        ultravox_cost DECIMAL(10, 4),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """
            }
        ]
        
        # Execute all queries in a transaction
        if await db.execute_transaction(queries):
            # Check if admin user exists
            admin_check = await db.execute("SELECT COUNT(*) as count FROM users WHERE username = 'admin'")
            if not admin_check or admin_check[0]['count'] == 0:
                # Hash the password before storing it
                hashed_password = hash_password('AFINasahbi@-11')
                await db.execute(
                    "INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (%s, %s, %s, %s)",
                    ('admin', hashed_password, True, True)
                )
            
            # Check if hamza user exists
            hamza_check = await db.execute("SELECT COUNT(*) as count FROM users WHERE username = 'hamza'")
            if not hamza_check or hamza_check[0]['count'] == 0:
                # Hash the password before storing it
                hashed_password = hash_password('AFINasahbi@-11')
                await db.execute(
                    "INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (%s, %s, %s, %s)",
                    ('hamza', hashed_password, True, True)
                )
                
            # Run the service tables migration if it exists
            migrations_path = os.path.join(os.path.dirname(__file__), 'migrations')
            service_tables_migration = os.path.join(migrations_path, 'create_service_tables.sql')
            data_sync_jobs_migration = os.path.join(migrations_path, 'add_data_sync_jobs_table.sql')
            
            if os.path.exists(service_tables_migration):
                await db.execute_migration(service_tables_migration)
                
            # Run the data sync jobs migration if it exists
            if os.path.exists(data_sync_jobs_migration):
                await db.execute_migration(data_sync_jobs_migration)
                
            logger.info("Database tables created successfully")
            return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        # Don't raise the exception, allow the app to continue without DB
        return False
