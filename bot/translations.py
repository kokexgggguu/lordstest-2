# Simple translation system
# In a production environment, you would use a proper translation service

TRANSLATIONS = {
    'pt': {
        'match_created': 'Partida criada com sucesso!',
        'match_reminder': 'Lembrete de partida',
        'match_starting_soon': 'A partida começará em breve',
        'invalid_permissions': 'Você não tem permissão para usar este comando',
        'channel_not_allowed': 'Este comando só pode ser usado em canais permitidos',
        'match_not_found': 'Partida não encontrada',
        'dm_sent': 'Mensagem privada enviada',
        'dm_failed': 'Falha ao enviar mensagem privada'
    },
    'es': {
        'match_created': '¡Partido creado exitosamente!',
        'match_reminder': 'Recordatorio de partido',
        'match_starting_soon': 'El partido comenzará pronto',
        'invalid_permissions': 'No tienes permiso para usar este comando',
        'channel_not_allowed': 'Este comando solo puede usarse en canales permitidos',
        'match_not_found': 'Partido no encontrado',
        'dm_sent': 'Mensaje privado enviado',
        'dm_failed': 'Error al enviar mensaje privado'
    },
    'en': {
        'match_created': 'Match created successfully!',
        'match_reminder': 'Match reminder',
        'match_starting_soon': 'Match will start soon',
        'invalid_permissions': 'You do not have permission to use this command',
        'channel_not_allowed': 'This command can only be used in allowed channels',
        'match_not_found': 'Match not found',
        'dm_sent': 'Private message sent',
        'dm_failed': 'Failed to send private message'
    },
    'ar': {
        'match_created': 'تم إنشاء المباراة بنجاح!',
        'match_reminder': 'تذكير بالمباراة',
        'match_starting_soon': 'ستبدأ المباراة قريباً',
        'invalid_permissions': 'ليس لديك صلاحية لاستخدام هذا الأمر',
        'channel_not_allowed': 'يمكن استخدام هذا الأمر فقط في القنوات المسموحة',
        'match_not_found': 'المباراة غير موجودة',
        'dm_sent': 'تم إرسال الرسالة الخاصة',
        'dm_failed': 'فشل في إرسال الرسالة الخاصة'
    }
}

def detect_language(text):
    """Simple language detection based on common patterns"""
    if any(char in text for char in 'ضصثقفغعهخحجچشسيبلاتنمكطئءؤرلاىةوزظذ'):
        return 'ar'
    elif any(word in text.lower() for word in ['vs', 'versus', 'against', 'team']):
        return 'en'
    elif any(word in text.lower() for word in ['vs', 'contra', 'equipo', 'partido']):
        return 'es'
    elif any(word in text.lower() for word in ['vs', 'contra', 'equipe', 'partida']):
        return 'pt'
    else:
        return 'en'  # Default to English

def get_translation(text, target_language):
    """Simple translation function - in production use a real translation service"""
    
    # Basic translation mappings
    translations = {
        'pt': {
            'New Match!': 'Nova Partida!',
            'Teams:': 'Equipes:',
            'Time:': 'Horário:',
            'A new match has been created and you were mentioned!': 'Uma nova partida foi criada e você foi mencionado!',
            'Match Reminder!': 'Lembrete de Partida!',
            'The match will start in': 'A partida começará em',
            'minutes': 'minutos',
            'Message from Server Admin': 'Mensagem do Administrador do Servidor'
        },
        'es': {
            'New Match!': '¡Nuevo Partido!',
            'Teams:': 'Equipos:',
            'Time:': 'Hora:',
            'A new match has been created and you were mentioned!': '¡Se ha creado un nuevo partido y has sido mencionado!',
            'Match Reminder!': '¡Recordatorio de Partido!',
            'The match will start in': 'El partido comenzará en',
            'minutes': 'minutos',
            'Message from Server Admin': 'Mensaje del Administrador del Servidor'
        },
        'ar': {
            'New Match!': 'مباراة جديدة!',
            'Teams:': 'الفرق:',
            'Time:': 'الوقت:',
            'A new match has been created and you were mentioned!': 'تم إنشاء مباراة جديدة وتم ذكرك فيها!',
            'Match Reminder!': 'تذكير بالمباراة!',
            'The match will start in': 'ستبدأ المباراة خلال',
            'minutes': 'دقائق',
            'Message from Server Admin': 'رسالة من مدير السيرفر'
        },
        'en': {}  # English is the base language
    }
    
    if target_language not in translations:
        return text
    
    # Simple word replacement
    translated = text
    for english, translation in translations[target_language].items():
        translated = translated.replace(english, translation)
    
    return translated
