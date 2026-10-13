var PiiMasker = Class.create();
PiiMasker.prototype = {
    initialize: function() {
        this.SCOPE = 'x_2229367_civicone';
    },

    /**
     * Detects and masks PII in grievance description.
     * Replaces Aadhaar numbers, PAN, phone numbers, email addresses.
     * Returns { maskedText, hasPii, detections }
     */
    maskPii: function(rawText) {
        if (!rawText) {
            return { maskedText: '', hasPii: false, detections: [] };
        }

        var text = String(rawText);
        var detections = [];

        // 1. Aadhaar Card Pattern (12 digits, often formatted as 4-4-4: 1234 5678 9012 or 1234-5678-9012)
        var aadhaarRegex = /\b(\d{4})[- ]?(\d{4})[- ]?(\d{4})\b/g;
        var matchAadhaar = text.match(aadhaarRegex);
        if (matchAadhaar) {
            detections.push('Aadhaar (' + matchAadhaar.length + ' found)');
            text = text.replace(aadhaarRegex, 'XXXX-XXXX-$3');
        }

        // 2. PAN Card Pattern (5 letters + 4 digits + 1 letter: ABCDE1234F)
        var panRegex = /\b([A-Z]{5})(\d{4})([A-Z]{1})\b/gi;
        var matchPan = text.match(panRegex);
        if (matchPan) {
            detections.push('PAN (' + matchPan.length + ' found)');
            text = text.replace(panRegex, function(m, p1, p2, p3) {
                return 'XXXXX' + p2 + p3.toUpperCase();
            });
        }

        // 3. Indian Phone Numbers (10 digits starting with 6-9, optional +91 or 0 prefix)
        var phoneRegex = /(?:\+91[\-\s]?|0)?\b([6-9]\d{5})(\d{4})\b/g;
        var matchPhone = text.match(phoneRegex);
        if (matchPhone) {
            detections.push('Phone (' + matchPhone.length + ' found)');
            text = text.replace(phoneRegex, 'XXXXXX$2');
        }

        // 4. Email Addresses
        var emailRegex = /\b([a-zA-Z0-9_\-\.]{1})[a-zA-Z0-9_\-\.]+@([a-zA-Z0-9_\-\.]+)\b/g;
        var matchEmail = text.match(emailRegex);
        if (matchEmail) {
            detections.push('Email (' + matchEmail.length + ' found)');
            text = text.replace(emailRegex, '$1***@$2');
        }

        return {
            maskedText: text,
            hasPii: detections.length > 0,
            detections: detections
        };
    },

    type: 'PiiMasker'
};
