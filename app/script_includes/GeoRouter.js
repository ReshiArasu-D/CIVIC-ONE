var GeoRouter = Class.create();
GeoRouter.prototype = {
    initialize: function() {
        this.SCOPE = 'x_2229367_civicone';
    },

    /**
     * Resolve ward from coordinates or address string.
     * Uses nearest civic asset proximity matching or deterministic fallback.
     */
    resolveWard: function(latitude, longitude, addressText) {
        var result = {
            ward: null,
            civic_asset: null,
            method: 'fallback'
        };

        // 1. Try finding closest civic asset with GPS coordinates
        if (latitude && longitude) {
            var lat = parseFloat(latitude);
            var lng = parseFloat(longitude);
            if (!isNaN(lat) && !isNaN(lng)) {
                var closest = this.findClosestAsset(lat, lng);
                if (closest && closest.ward) {
                    result.ward = closest.ward;
                    result.civic_asset = closest.sys_id;
                    result.method = 'gps_proximity';
                    return result;
                }
            }
        }

        // 2. Try address keyword matching against Ward names
        if (addressText) {
            var wardGr = new GlideRecord(this.SCOPE + '_ward');
            wardGr.addQuery('active', true);
            wardGr.query();

            while (wardGr.next()) {
                var wName = wardGr.getValue('name') || '';
                var wCode = wardGr.getValue('code') || '';
                if (addressText.toLowerCase().indexOf(wName.toLowerCase()) >= 0 ||
                    addressText.toUpperCase().indexOf(wCode.toUpperCase()) >= 0) {
                    result.ward = wardGr.getUniqueValue();
                    result.method = 'address_match';
                    return result;
                }
            }
        }

        // 3. Deterministic Fallback: Default to central headquarters ward
        var fallbackWard = new GlideRecord(this.SCOPE + '_ward');
        fallbackWard.addQuery('active', true);
        fallbackWard.orderBy('ward_number');
        fallbackWard.setLimit(1);
        fallbackWard.query();

        if (fallbackWard.next()) {
            result.ward = fallbackWard.getUniqueValue();
            result.method = 'deterministic_fallback';
        }

        return result;
    },

    /**
     * Find civic asset closest to coordinates within threshold.
     */
    findClosestAsset: function(lat, lng) {
        var assetGr = new GlideRecord(this.SCOPE + '_civic_asset');
        assetGr.addNotNullQuery('latitude');
        assetGr.addNotNullQuery('longitude');
        assetGr.query();

        var closest = null;
        var minDistance = 999999.0;

        while (assetGr.next()) {
            var aLat = parseFloat(assetGr.getValue('latitude'));
            var aLng = parseFloat(assetGr.getValue('longitude'));
            if (!isNaN(aLat) && !isNaN(aLng)) {
                // Approximate Euclidean distance for local jurisdiction
                var dLat = lat - aLat;
                var dLng = lng - aLng;
                var dist = Math.sqrt(dLat * dLat + dLng * dLng);
                if (dist < minDistance) {
                    minDistance = dist;
                    closest = {
                        sys_id: assetGr.getUniqueValue(),
                        ward: assetGr.getValue('ward'),
                        name: assetGr.getValue('name')
                    };
                }
            }
        }
        return closest;
    },

    type: 'GeoRouter'
};
