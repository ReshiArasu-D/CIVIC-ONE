var JurisdictionUtil = Class.create();
JurisdictionUtil.prototype = {
    initialize: function() {
        this.SCOPE = 'x_2229367_civicone';
    },

    /**
     * Resolve full hierarchy from Ward sys_id.
     * Returns { ward, sub_district, district, state, zone } sys_ids.
     */
    resolveHierarchyFromWard: function(wardSysId) {
        if (!wardSysId) return null;

        var result = {
            ward: wardSysId,
            sub_district: null,
            district: null,
            state: null,
            zone: null
        };

        var wardGr = new GlideRecord(this.SCOPE + '_ward');
        if (wardGr.get(wardSysId)) {
            var subDistrictId = wardGr.getValue('sub_district');
            result.sub_district = subDistrictId;

            if (subDistrictId) {
                var subGr = new GlideRecord(this.SCOPE + '_sub_district');
                if (subGr.get(subDistrictId)) {
                    var districtId = subGr.getValue('district');
                    result.district = districtId;

                    if (districtId) {
                        var distGr = new GlideRecord(this.SCOPE + '_district');
                        if (distGr.get(districtId)) {
                            var stateId = distGr.getValue('state');
                            result.state = stateId;

                            if (stateId) {
                                var stateGr = new GlideRecord(this.SCOPE + '_state');
                                if (stateGr.get(stateId)) {
                                    result.zone = stateGr.getValue('zone');
                                }
                            }
                        }
                    }
                }
            }
        }
        return result;
    },

    /**
     * Check if a case worker is authorized for a specific ward / department.
     */
    isWorkerAuthorized: function(workerUserSysId, wardSysId, deptSysId) {
        if (!workerUserSysId) return false;

        var workerGr = new GlideRecord(this.SCOPE + '_case_worker');
        workerGr.addQuery('user', workerUserSysId);
        workerGr.addQuery('is_available', true);
        if (deptSysId) {
            workerGr.addQuery('department', deptSysId);
        }
        workerGr.query();

        while (workerGr.next()) {
            var workerWard = workerGr.getValue('ward');
            if (!workerWard || workerWard === wardSysId) {
                return true;
            }
            // Check sub-district match
            var hier = this.resolveHierarchyFromWard(wardSysId);
            if (hier && hier.sub_district && workerGr.getValue('sub_district') === hier.sub_district) {
                return true;
            }
            if (hier && hier.district && workerGr.getValue('district') === hier.district) {
                return true;
            }
        }
        return false;
    },

    /**
     * Find best eligible case worker for ward and department.
     * Orders by lowest active case load.
     */
    findEligibleWorker: function(wardSysId, deptSysId) {
        var workerGr = new GlideRecord(this.SCOPE + '_case_worker');
        workerGr.addQuery('department', deptSysId);
        workerGr.addQuery('is_available', true);
        workerGr.addQuery('ward', wardSysId);
        workerGr.orderBy('active_case_load');
        workerGr.query();

        if (workerGr.next()) {
            return workerGr.getValue('user');
        }

        // Fallback: check sub-district level workers
        var hier = this.resolveHierarchyFromWard(wardSysId);
        if (hier && hier.sub_district) {
            var subWorkerGr = new GlideRecord(this.SCOPE + '_case_worker');
            subWorkerGr.addQuery('department', deptSysId);
            subWorkerGr.addQuery('is_available', true);
            subWorkerGr.addQuery('sub_district', hier.sub_district);
            subWorkerGr.orderBy('active_case_load');
            subWorkerGr.query();

            if (subWorkerGr.next()) {
                return subWorkerGr.getValue('user');
            }
        }

        return null;
    },

    type: 'JurisdictionUtil'
};
