// translations.js - Contains translation strings for the application

const translations = {
  // English translations
  en: {
    // Navigation
    dashboard: 'Dashboard',
    calls: 'Call Manager',
    callHistory: 'Call History',
    knowledge: 'Knowledge Base',
    services: 'Service Connections',
    settings: 'System Configuration',
    users: 'User Management',
    export: 'Export Data',
    analytics: 'Analytics',
    
    // Dashboard
    quickActions: 'Quick Actions',
    callCapacity: 'Call Capacity',
    activeServices: 'Active Services',
    systemHealth: 'System Health',
    
    // Call Manager
    callManagement: 'Call Management',
    bulkCallInterface: 'Bulk Call Interface',
    outboundCalls: 'Outbound Calls',
    inboundCalls: 'Inbound Calls',
    enterPhoneNumbers: 'Enter phone numbers (one per line)',
    initiateCalls: 'Initiate Calls',
    configureYourTwilio: 'Configure your Twilio webhook with the following URL:',
    selectVoice: 'Select Voice',
    existingClients: 'Existing Clients',
    addClient: 'Add Client',
    updateClient: 'Update Client',
    callSelected: 'Call Selected',
    name: 'Name',
    phoneNumber: 'Phone Number',
    email: 'Email',
    address: 'Address',
    actions: 'Actions',
    
    // Call Capacity
    liveData: 'Live',
    theoretical: 'Theoretical',
    recommendedOutboundCalls: 'Recommended Outbound Calls',
    maxInboundCalls: 'Max Inbound Calls',
    callsPerMinute: 'Calls Per Minute',
    limitingFactor: 'Limiting Factor',
    maxConcurrentCalls: 'Max Concurrent Calls',
    
    // Common Actions
    refresh: 'Refresh',
    retry: 'Retry',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    
    // Auth
    login: 'Login',
    logout: 'Logout',
    register: 'Register',
    forgotPassword: 'Forgot Password',
    
    // Status
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Information',
    loading: 'Loading'
  },
  
  // French translations
  fr: {
    // Navigation
    dashboard: 'Tableau de Bord',
    calls: 'Gestionnaire d\'Appels',
    callHistory: 'Historique des Appels',
    knowledge: 'Base de Connaissances',
    services: 'Connexions de Service',
    settings: 'Configuration du Système',
    users: 'Gestion des Utilisateurs',
    export: 'Exporter les Données',
    analytics: 'Analytique',
    
    // Dashboard
    quickActions: 'Actions Rapides',
    callCapacity: 'Capacité d\'Appel',
    activeServices: 'Services Actifs',
    systemHealth: 'État du Système',
    
    // Call Capacity
    liveData: 'En Direct',
    theoretical: 'Théorique',
    recommendedOutboundCalls: 'Appels Sortants Recommandés',
    maxInboundCalls: 'Max Appels Entrants',
    callsPerMinute: 'Appels Par Minute',
    limitingFactor: 'Facteur Limitant',
    maxConcurrentCalls: 'Max Appels Simultanés',
    
    // Common Actions
    refresh: 'Actualiser',
    retry: 'Réessayer',
    save: 'Enregistrer',
    cancel: 'Annuler',
    delete: 'Supprimer',
    edit: 'Modifier',
    add: 'Ajouter',
    
    // Auth
    login: 'Connexion',
    logout: 'Déconnexion',
    register: 'S\'inscrire',
    forgotPassword: 'Mot de Passe Oublié',
    
    // Status
    success: 'Succès',
    error: 'Erreur',
    warning: 'Avertissement',
    info: 'Information',
    loading: 'Chargement'
  },
  
  // Arabic translations
  ar: {
    // Navigation
    dashboard: 'لوحة المعلومات',
    calls: 'مدير المكالمات',
    callHistory: 'سجل المكالمات',
    knowledge: 'قاعدة المعرفة',
    services: 'خدمات الاتصال',
    settings: 'إعدادات النظام',
    users: 'إدارة المستخدمين',
    export: 'تصدير البيانات',
    analytics: 'تحليلات',
    
    // Dashboard
    quickActions: 'إجراءات سريعة',
    callCapacity: 'سعة المكالمات',
    activeServices: 'الخدمات النشطة',
    systemHealth: 'حالة النظام',
    
    // Call Capacity
    liveData: 'مباشر',
    theoretical: 'نظري',
    recommendedOutboundCalls: 'المكالمات الصادرة الموصى بها',
    maxInboundCalls: 'الحد الأقصى للمكالمات الواردة',
    callsPerMinute: 'المكالمات في الدقيقة',
    limitingFactor: 'العامل المحدد',
    maxConcurrentCalls: 'الحد الأقصى للمكالمات المتزامنة',
    
    // Common Actions
    refresh: 'تحديث',
    retry: 'إعادة المحاولة',
    save: 'حفظ',
    cancel: 'إلغاء',
    delete: 'حذف',
    edit: 'تعديل',
    add: 'إضافة',
    
    // Auth
    login: 'تسجيل الدخول',
    logout: 'تسجيل الخروج',
    register: 'تسجيل',
    forgotPassword: 'نسيت كلمة المرور',
    
    // Status
    success: 'نجاح',
    error: 'خطأ',
    warning: 'تحذير',
    info: 'معلومات',
    loading: 'جاري التحميل'
  }
};

export default translations;
