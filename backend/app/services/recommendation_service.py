from typing import List, Dict, Any

class RecommendationService:
    @staticmethod
    def generate_recommendations(project_data: Dict[str, Any]) -> List[str]:
        """Generates clear, actionable recommendations based on project metrics."""
        recs = []
        
        testing_cov = float(project_data.get("testing_coverage", 0.0))
        bug_count = int(project_data.get("bug_count", 0))
        req_changes = int(project_data.get("requirement_changes", 0))
        sprint_delays = int(project_data.get("sprint_delays", 0))
        team_exp = float(project_data.get("team_experience_years", 0.0))
        client_inv = int(project_data.get("client_involvement", 3))
        res_avail = float(project_data.get("resource_availability", 100.0))
        cust_sat = int(project_data.get("customer_satisfaction", 3))
        budget = float(project_data.get("budget", 0.0))
        duration = int(project_data.get("duration_days", 0))
        team_size = int(project_data.get("team_size", 0))
        
        # 1. Code Quality & Testing
        if testing_cov < 70.0:
            recs.append(
                f"Increase testing coverage: Code coverage is currently at {testing_cov}%. "
                "Aim for a minimum threshold of 80% to lower regression bugs."
            )
        elif testing_cov < 85.0 and bug_count > 30:
            recs.append(
                "Strengthen integration testing: Testing coverage is moderate, but active bugs are high. "
                "Add end-to-end automated UI or regression test suites."
            )
            
        # 2. Scope Creep
        if req_changes > 4:
            recs.append(
                f"Freeze project scope: The project has experienced {req_changes} requirement changes. "
                "Implement a strict change management workflow and review project boundaries with stakeholders."
            )
            
        # 3. Execution & Delivery delays
        if sprint_delays > 3:
            recs.append(
                f"Re-evaluate sprint capacity: The team has logged {sprint_delays} delayed sprints. "
                "Reduce sprint commitments by 20% in the next planning meeting to align with actual velocity."
            )
            
        # 4. Team Capability
        if team_exp < 3.0:
            recs.append(
                f"Onboard expert developers: Average team experience is {team_exp} years. "
                "Consider pairing junior developers with a senior technical architect or mentor."
            )
            
        # 5. Client Involvement
        if client_inv < 3:
            recs.append(
                f"Increase client involvement: Current client involvement score is {client_inv}/5. "
                "Establish bi-weekly showcase sessions or sprint demo reviews to secure early alignment."
            )
            
        # 6. Resource constraints
        if res_avail < 80.0:
            recs.append(
                f"Mitigate resource constraints: Team resource availability is at {res_avail}%. "
                "Arrange backup staff, or cross-train existing members to cover specialized technical fields."
            )
            
        # 7. Bug backlog
        if bug_count > 40:
            recs.append(
                f"Conduct a bug-squashing sprint: Active bug count is high ({bug_count}). "
                "Dedicating the next entire sprint purely to fixing high-severity bugs before adding new features is highly recommended."
            )
            
        # 8. Customer Satisfaction
        if cust_sat < 3:
            recs.append(
                f"Gather detailed end-user feedback: User satisfaction is low ({cust_sat}/5). "
                "Conduct feedback surveys or user interviews to identify usability gaps."
            )
            
        # 9. Burn rate check
        if team_size > 0 and duration > 0:
            burn_estimate = (team_size * 500.0) * (duration / 30.0) # Assume $500/developer/month average cost proxy
            if budget < burn_estimate:
                recs.append(
                    f"Audit budget and burn rate: The budget of ${budget:,.2f} is tight relative to "
                    f"a team size of {team_size} over {duration} days. Monitor resource burn rates closely."
                )

        # Default fallbacks if no specific alerts trigger
        if not recs:
            recs.append("Maintain current project execution parameters. Continue monitoring code quality and sprint velocities.")
            recs.append("Conduct a mid-project review with the team to identify optimization areas before the next release cycle.")
            
        return recs
