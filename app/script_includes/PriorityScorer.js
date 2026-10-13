var PriorityScorer = Class.create();
PriorityScorer.prototype = {
    initialize: function() {
        this.SCOPE = 'x_2229367_civicone';
    },

    /**
     * Calculate priority score (0 - 100) and mapped ServiceNow priority (1 - 4).
     * Deterministic calculation:
     * - Base category weight: 20 - 40 pts
     * - Hazard & safety severity keywords: 0 - 30 pts
     * - Public infrastructure impact: 0 - 20 pts
     * - Vulnerability indicators: 0 - 10 pts
     */
    calculatePriority: function(categorySysId, descriptionText, urgencyChoice) {
        var score = 0;
        var factors = [];

        // 1. Category Base Weight
        if (categorySysId) {
            var catGr = new GlideRecord(this.SCOPE + '_category');
            if (catGr.get(categorySysId)) {
                var catUrgency = catGr.getValue('default_urgency');
                if (catUrgency == '1') {
                    score += 40;
                    factors.push('High-urgency Category (+40)');
                } else if (catUrgency == '2') {
                    score += 25;
                    factors.push('Medium-urgency Category (+25)');
                } else {
                    score += 15;
                    factors.push('Standard Category (+15)');
                }
            }
        } else {
            score += 20;
        }

        // 2. Hazard & Safety Severity Analysis
        var text = (descriptionText || '').toLowerCase();
        var hazardKeywords = [
            'gas leak', 'live wire', 'electrocution', 'contamination', 'flood',
            'collapse', 'fire', 'sewage overflow', 'toxic', 'broken pipeline',
            'drowning', 'sinkhole', 'blast', 'short circuit'
        ];
        var foundHazards = 0;
        for (var i = 0; i < hazardKeywords.length; i++) {
            if (text.indexOf(hazardKeywords[i]) >= 0) {
                foundHazards++;
            }
        }
        if (foundHazards >= 2) {
            score += 30;
            factors.push('Severe Multi-hazard detected (+30)');
        } else if (foundHazards === 1) {
            score += 20;
            factors.push('Hazard keyword detected (+20)');
        }

        // 3. Public Infrastructure Impact
        var infraKeywords = ['hospital', 'school', 'clinic', 'main road', 'highway', 'market', 'railway station', 'bus stand'];
        for (var j = 0; j < infraKeywords.length; j++) {
            if (text.indexOf(infraKeywords[j]) >= 0) {
                score += 15;
                factors.push('Critical Infrastructure (' + infraKeywords[j] + ') (+15)');
                break;
            }
        }

        // 4. Vulnerable Citizen Indicators
        var vulnKeywords = ['elderly', 'senior citizen', 'infant', 'child', 'disabled', 'handicapped', 'pregnant'];
        for (var k = 0; k < vulnKeywords.length; k++) {
            if (text.indexOf(vulnKeywords[k]) >= 0) {
                score += 10;
                factors.push('Vulnerable population impacted (+10)');
                break;
            }
        }

        // 5. Intake Urgency Adjustment
        if (urgencyChoice == '1') {
            score += 10;
            factors.push('Direct High Urgency selected (+10)');
        }

        // Bound score to 0 - 100
        score = Math.min(100, Math.max(0, score));

        // Map to ServiceNow Task Priority (1: Critical, 2: High, 3: Moderate, 4: Low)
        var mappedPriority = 4;
        if (score >= 80) {
            mappedPriority = 1;
        } else if (score >= 60) {
            mappedPriority = 2;
        } else if (score >= 40) {
            mappedPriority = 3;
        } else {
            mappedPriority = 4;
        }

        return {
            score: score,
            priority: mappedPriority,
            factors: factors
        };
    },

    type: 'PriorityScorer'
};
