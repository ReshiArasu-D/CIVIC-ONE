var AiLogger = Class.create();
AiLogger.prototype = {
    initialize: function() {
        this.SCOPE = 'x_2229367_civicone';
    },

    /**
     * Audit logger for AI & Rule Engine actions.
     * Implements strict audit contract required for governance.
     */
    logAction: function(params) {
        /*
          params = {
            case_id: sys_id,
            action_type: 'Priority Scoring' | 'Routing Suggestion' | 'Duplicate Detection' | 'PII Masking',
            agent_name: 'RuleEngine:PriorityScorer',
            input_payload: JSON or string,
            output_payload: JSON or string,
            confidence_score: 0.95,
            execution_status: 'Success' | 'Fallback' | 'Error' | 'Skipped',
            applied_to_case: true,
            review_required: false
          }
        */
        if (!params) return null;

        var logGr = new GlideRecord(this.SCOPE + '_ai_action_log');
        logGr.initialize();

        if (params.case_id) logGr.setValue('case', params.case_id);
        if (params.action_type) logGr.setValue('action_type', params.action_type);
        if (params.agent_name) logGr.setValue('agent_name', params.agent_name);
        
        var inputStr = typeof params.input_payload === 'object' ? JSON.stringify(params.input_payload) : (params.input_payload || '');
        var outputStr = typeof params.output_payload === 'object' ? JSON.stringify(params.output_payload) : (params.output_payload || '');
        
        logGr.setValue('input_payload', inputStr.substring(0, 3999));
        logGr.setValue('output_payload', outputStr.substring(0, 3999));
        
        if (params.confidence_score !== undefined) logGr.setValue('confidence_score', params.confidence_score);
        logGr.setValue('execution_status', params.execution_status || 'Success');
        logGr.setValue('applied_to_case', params.applied_to_case !== false);
        logGr.setValue('review_required', params.review_required === true);
        
        var nowGdt = new GlideDateTime();
        logGr.setValue('audit_timestamp', nowGdt);

        var id = logGr.insert();
        return id;
    },

    type: 'AiLogger'
};
