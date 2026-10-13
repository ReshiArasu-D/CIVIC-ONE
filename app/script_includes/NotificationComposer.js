var NotificationComposer = Class.create();
NotificationComposer.prototype = {
    initialize: function() {
        this.SCOPE = 'x_2229367_civicone';
    },

    /**
     * Compose localized notification message from template and context data.
     * Tokens in template: {case_number}, {citizen_name}, {category}, {status}, {ward}, {sla_hours}
     */
    composeNotification: function(templateCode, citizenSysId, contextTokens) {
        var result = {
            subject: '',
            body: '',
            channel: 'In-App',
            language_code: 'en',
            composed: false
        };

        // 1. Resolve Citizen Preferred Language
        var langSysId = null;
        var langCode = 'en';

        if (citizenSysId) {
            var citGr = new GlideRecord(this.SCOPE + '_customer');
            if (citGr.get(citizenSysId)) {
                langSysId = citGr.getValue('preferred_language');
            }
        }

        if (langSysId) {
            var langGr = new GlideRecord(this.SCOPE + '_language');
            if (langGr.get(langSysId)) {
                langCode = langGr.getValue('code') || 'en';
            }
        }

        result.language_code = langCode;

        // 2. Fetch Notification Template
        var tmplGr = new GlideRecord(this.SCOPE + '_notification_template');
        tmplGr.addQuery('code', templateCode);
        if (langSysId) {
            tmplGr.addQuery('language', langSysId);
        }
        tmplGr.addQuery('active', true);
        tmplGr.query();

        if (!tmplGr.next()) {
            // Fallback to English template
            tmplGr = new GlideRecord(this.SCOPE + '_notification_template');
            tmplGr.addQuery('code', templateCode);
            tmplGr.addQuery('active', true);
            tmplGr.query();
            if (!tmplGr.next()) {
                // Hardcoded universal fallback
                result.subject = 'CivicOne Update: ' + (contextTokens.case_number || 'Your Case');
                result.body = 'Your grievance ' + (contextTokens.case_number || '') + ' status has been updated to: ' + (contextTokens.status || 'Updated') + '.';
                result.composed = true;
                return result;
            }
        }

        var subjectStr = tmplGr.getValue('subject') || '';
        var bodyStr = tmplGr.getValue('body_template') || '';
        result.channel = tmplGr.getValue('channel') || 'In-App';

        // 3. Substitute Tokens
        if (contextTokens) {
            for (var key in contextTokens) {
                var regex = new RegExp('\\{' + key + '\\}', 'g');
                var val = contextTokens[key] || '';
                subjectStr = subjectStr.replace(regex, val);
                bodyStr = bodyStr.replace(regex, val);
            }
        }

        result.subject = subjectStr;
        result.body = bodyStr;
        result.composed = true;
        return result;
    },

    type: 'NotificationComposer'
};
