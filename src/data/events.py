"""
Static decision events for the 8-quarter startup simulation.

~20 starter events per sector + 20 universal + 20 shock events.
Each event has 3 choices with AP cost, stat/financial effects, and reaction text.

Effects dict keys:
  - stat deltas:  {"growth": +2, "tech": -1}
  - financial:    {"cash": -5000, "burn_rate": +2000, "revenue": +3000}
  - special:      {"valuation_mult": 1.1, "equity": +2.0, "traction_users": +500}
"""

from __future__ import annotations
from typing import Any, Dict, List


def _ev(
    id: str,
    title: str,
    description: str,
    department: str,
    sector: str | None,
    phase: str,
    choices: list,
    is_shock: bool = False,
) -> Dict[str, Any]:
    return {
        "id": id,
        "title": title,
        "description": description,
        "department": department,
        "sector": sector,
        "phase": phase,
        "choices": choices,
        "is_shock": is_shock,
    }


def _ch(text: str, ap_cost: int = 1, effects: dict | None = None, reaction: str = "") -> Dict[str, Any]:
    return {"text": text, "ap_cost": ap_cost, "effects": effects or {}, "reaction": reaction}


# ═══════════════════════════════════════════════════════════════════
# UNIVERSAL EVENTS (any sector)
# ═══════════════════════════════════════════════════════════════════

UNIVERSAL_EVENTS: List[Dict[str, Any]] = [
    _ev("UNI-001", "Office Lease Decision",
        "Your current co-working space is getting cramped. A real office just opened up nearby at 3x the cost.",
        "ops", None, "early",
        [
            _ch("Sign the lease — room to grow", 2, {"burn_rate": 4000, "ops": 2, "brand": 1, "execution": 1}, "The team loves the new space. Productivity is up."),
            _ch("Stay in co-working — save cash", 1, {"ops": -1}, "It's tight, but the runway matters more right now."),
            _ch("Go fully remote", 1, {"burn_rate": -2000, "tech": 1, "ops": -1}, "Some team members thrive; others feel disconnected."),
        ]),

    _ev("UNI-002", "First Media Feature",
        "A popular tech blog wants to write about your startup. They want an exclusive interview.",
        "brand", None, "early",
        [
            _ch("Go all in — prep a full media kit", 2, {"brand": 3, "growth": 2, "cash": -3000}, "The article goes semi-viral. Inbound leads spike."),
            _ch("Quick phone interview — minimal effort", 1, {"brand": 1, "growth": 1}, "Decent coverage. A few new signups trickle in."),
            _ch("Decline — stay in stealth mode", 0, {}, "You stay under the radar. No upside, no downside."),
        ]),

    _ev("UNI-003", "Co-founder Disagreement",
        "Your co-founder wants to pivot the product direction significantly. The team is split.",
        "product", None, "early",
        [
            _ch("Support the pivot — trust your co-founder", 2, {"product": 2, "innovation": 2, "execution": -2}, "The pivot energizes the team but delays the roadmap by weeks."),
            _ch("Compromise — merge both visions", 2, {"product": 1, "innovation": 1, "execution": -1}, "A middle ground emerges. Not everyone is happy, but it works."),
            _ch("Reject the pivot — stay the course", 1, {"execution": 2, "innovation": -1}, "You keep momentum but your co-founder is frustrated."),
        ]),

    _ev("UNI-004", "Key Employee Threatens to Leave",
        "Your lead developer just got an offer from Google at 2x their salary. They want a counteroffer.",
        "ops", None, "early",
        [
            _ch("Match the offer + equity sweetener", 2, {"cash": -8000, "burn_rate": 3000, "tech": 2, "execution": 1}, "They stay. Morale across the team improves."),
            _ch("Offer equity only — no cash raise", 1, {"equity": 1.5, "tech": 1}, "They stay tentatively. They'll revisit in 6 months."),
            _ch("Wish them well — hire a replacement", 1, {"tech": -2, "execution": -1, "cash": -5000}, "You lose institutional knowledge but save on long-term costs."),
        ]),

    _ev("UNI-005", "Investor Coffee Chat",
        "An angel investor DMs you on LinkedIn. They're interested but want to grab coffee first.",
        "finance", None, "early",
        [
            _ch("Prepare a full pitch deck", 2, {"finance": 2, "brand": 1, "cash": 15000}, "They write a $15K check on the spot. Nice."),
            _ch("Casual chat — feel them out", 1, {"finance": 1}, "Good connection. They say they'll 'follow your progress.'"),
            _ch("Too busy right now — rain check", 0, {}, "You never hear from them again."),
        ]),

    _ev("UNI-006", "Hackathon Opportunity",
        "A major tech company is hosting a hackathon with a $50K grand prize. Your team wants to enter.",
        "tech", None, "early",
        [
            _ch("Send your best engineers", 2, {"tech": 2, "innovation": 2, "brand": 1, "execution": -1}, "You win 2nd place! Great press and a $20K prize."),
            _ch("Send junior team members for experience", 1, {"tech": 1, "innovation": 1}, "They don't place but learn a lot and make connections."),
            _ch("Skip it — focus on product", 1, {"execution": 1}, "Heads down. The product inches forward."),
        ]),

    _ev("UNI-007", "Customer Support Crisis",
        "Your biggest customer is threatening to churn. They're frustrated with response times and bugs.",
        "ops", None, "early",
        [
            _ch("Assign a dedicated account manager", 2, {"ops": 2, "brand": 1, "burn_rate": 2000, "revenue": 5000}, "The customer renews and even upgrades their plan."),
            _ch("Rush a bug-fix sprint", 2, {"tech": 1, "product": 1, "execution": -1}, "Bugs squashed. Customer is mollified but still wary."),
            _ch("Apologize and offer a discount", 1, {"revenue": -2000, "brand": -1}, "They stay but you've set a bad precedent."),
        ]),

    _ev("UNI-008", "Partnership Proposal",
        "A mid-size company proposes a co-marketing deal. They have 50K users in your target demo.",
        "growth", None, "early",
        [
            _ch("Full integration partnership", 2, {"growth": 3, "brand": 2, "tech": -1, "traction_users": 2000}, "User acquisition spikes! But integration debt piles up."),
            _ch("Light co-marketing only", 1, {"growth": 1, "brand": 1, "traction_users": 500}, "Modest uplift. Low effort, low reward."),
            _ch("Decline — protect the brand", 0, {"brand": 1}, "You keep brand purity. The opportunity passes."),
        ]),

    _ev("UNI-009", "Legal Scare",
        "A competitor's lawyer sends a cease-and-desist letter claiming you infringe on their patent.",
        "ops", None, "late",
        [
            _ch("Hire a patent lawyer — fight it", 2, {"cash": -12000, "ops": 1, "brand": 1}, "Your lawyer shuts them down. The claim was weak."),
            _ch("Pivot the feature to avoid conflict", 2, {"product": -1, "tech": 1, "innovation": 1}, "You redesign the feature. It's actually better now."),
            _ch("Ignore it — call their bluff", 0, {"ops": -2, "brand": -1}, "They escalate. Legal costs mount next quarter."),
        ]),

    _ev("UNI-010", "Acquisition Offer",
        "A large company offers to acqui-hire your team for $500K. It's a sure exit but kills the vision.",
        "finance", None, "late",
        [
            _ch("Decline — we're building something bigger", 1, {"execution": 2, "innovation": 1}, "The team rallies around the long-term mission."),
            _ch("Counter with a higher number", 2, {"finance": 2, "brand": 1}, "They come back at $750K. You still decline, but it boosts credibility."),
            _ch("Seriously consider it", 1, {"finance": -1, "execution": -1}, "The deliberation distracts the team for weeks."),
        ]),

    _ev("UNI-011", "Conference Speaking Slot",
        "You've been invited to speak at a major industry conference. Ticket + travel = $5K.",
        "brand", None, "early",
        [
            _ch("Accept — great visibility", 2, {"brand": 3, "growth": 1, "cash": -5000}, "Your talk goes viral on Twitter. New leads pour in."),
            _ch("Send a team member instead", 1, {"brand": 1, "cash": -3000}, "Good networking but less impact without the CEO."),
            _ch("Decline — too expensive right now", 0, {}, "You miss the opportunity. Nothing changes."),
        ]),

    _ev("UNI-012", "Technical Debt Reckoning",
        "Your codebase is held together with duct tape. The CTO warns: refactor now or pay later.",
        "tech", None, "late",
        [
            _ch("Full refactor sprint — 2 weeks", 2, {"tech": 3, "execution": 2, "product": -1}, "Clean code. Deployment speed doubles. Worth it."),
            _ch("Incremental cleanup", 1, {"tech": 1, "execution": 1}, "Gradual improvement. At least it's not getting worse."),
            _ch("Ship features, worry later", 1, {"product": 1, "tech": -2}, "New features land but every deploy is a prayer."),
        ]),

    _ev("UNI-013", "Viral Social Media Moment",
        "A meme featuring your product goes viral. 100K impressions in 24 hours.",
        "growth", None, "early",
        [
            _ch("Capitalize — launch a flash sale", 2, {"growth": 3, "revenue": 8000, "brand": 2, "traction_users": 3000}, "Revenue spikes. You convert 5% of the traffic."),
            _ch("Engage organically — ride the wave", 1, {"growth": 2, "brand": 1, "traction_users": 1000}, "Decent engagement. Brand awareness up."),
            _ch("Ignore it — it's just noise", 0, {"growth": -1}, "The moment passes. Your competitors notice you didn't."),
        ]),

    _ev("UNI-014", "Board Member Introduction",
        "Your investor introduces you to a Fortune 500 VP who could be your first enterprise client.",
        "finance", None, "late",
        [
            _ch("Full enterprise pitch — build custom demo", 2, {"finance": 2, "product": 1, "revenue": 15000, "cash": -3000}, "They sign a $60K annual contract! Game changer."),
            _ch("Standard demo — see if they bite", 1, {"finance": 1, "revenue": 5000}, "Interested but want more features. Pipeline building."),
            _ch("Not ready for enterprise yet", 0, {"execution": 1}, "You focus on SMB. Enterprise can wait."),
        ]),

    _ev("UNI-015", "Team Burnout Warning",
        "Your team has been grinding 60-hour weeks. Morale is dropping. Someone cried in the bathroom.",
        "ops", None, "late",
        [
            _ch("Mandatory week off + team retreat", 2, {"cash": -6000, "ops": 2, "execution": 2, "brand": 1}, "The team comes back recharged and more loyal."),
            _ch("Flex Fridays — work from anywhere", 1, {"ops": 1, "execution": 1}, "Small improvement. At least people can breathe."),
            _ch("Push through — we're almost there", 0, {"execution": -2, "ops": -1, "tech": -1}, "Two people quietly update their LinkedIn."),
        ]),

    _ev("UNI-016", "Government Grant Opportunity",
        "A government innovation grant offers up to $50K for startups in your domain. Application takes work.",
        "finance", None, "early",
        [
            _ch("Full application — dedicate a week", 2, {"cash": 35000, "finance": 2, "innovation": 1}, "You win the grant! Non-dilutive cash."),
            _ch("Quick application — minimal effort", 1, {"cash": 10000, "finance": 1}, "Partial grant awarded. Better than nothing."),
            _ch("Skip — not worth the distraction", 0, {}, "Free money left on the table. Focus stays on product."),
        ]),

    _ev("UNI-017", "Data Breach Scare",
        "Your security audit reveals a vulnerability. No data was stolen — yet.",
        "tech", None, "late",
        [
            _ch("Emergency security overhaul", 2, {"tech": 3, "ops": 1, "cash": -8000, "product": -1}, "Vulnerability patched. You publish a transparency report."),
            _ch("Quick patch + monitoring", 1, {"tech": 1, "cash": -2000}, "Patched for now. You'll do a proper audit next quarter."),
            _ch("Monitor but don't act yet", 0, {"tech": -1, "brand": -2}, "A reporter finds out. Not a great look."),
        ]),

    _ev("UNI-018", "Pricing Strategy Debate",
        "Sales wants to lower prices to drive volume. Product wants to raise prices for positioning.",
        "product", None, "late",
        [
            _ch("Lower prices — volume play", 2, {"growth": 3, "revenue": -3000, "brand": -1, "traction_users": 2000}, "More users, but margins thin. Growth metrics look great."),
            _ch("Raise prices — premium positioning", 2, {"brand": 2, "finance": 2, "revenue": 5000, "growth": -1}, "Fewer signups but much better unit economics."),
            _ch("Introduce a freemium tier", 1, {"growth": 2, "product": 1, "burn_rate": 2000, "traction_users": 1500}, "Free users flood in. Conversion rate TBD."),
        ]),

    _ev("UNI-019", "Competitor Launches Similar Feature",
        "Your main competitor just shipped a feature you've been building for months. They beat you to market.",
        "product", None, "late",
        [
            _ch("Ship faster — cut corners to launch this week", 2, {"product": 1, "execution": 2, "tech": -2}, "You launch! Buggy, but you're in the race."),
            _ch("Differentiate — add a unique twist before launch", 2, {"product": 2, "innovation": 2}, "Your version is clearly better. Reviews notice."),
            _ch("Pivot to a different feature entirely", 1, {"innovation": 2, "product": -1, "execution": -1}, "New direction. Risky, but potentially more defensible."),
        ]),

    _ev("UNI-020", "International Expansion Opportunity",
        "A distributor in Europe wants to bring your product to the EU market. Regulatory compliance needed.",
        "growth", None, "late",
        [
            _ch("Full EU launch — GDPR compliance + localization", 2, {"growth": 3, "brand": 2, "cash": -15000, "ops": 1, "revenue": 10000}, "EU launch succeeds! Revenue diversification achieved."),
            _ch("Pilot in one country first", 1, {"growth": 1, "cash": -5000, "revenue": 3000}, "UK pilot goes well. Others will follow."),
            _ch("Not ready — focus on home market", 0, {"execution": 1}, "You stay focused. International can wait."),
        ]),
]


# ═══════════════════════════════════════════════════════════════════
# SECTOR-SPECIFIC EVENTS
# ═══════════════════════════════════════════════════════════════════

AI_EVENTS: List[Dict[str, Any]] = [
    _ev("AI-001", "GPU Shortage",
        "NVIDIA's latest GPUs are backordered 6 months. Your model training pipeline is at risk.",
        "tech", "AI", "early",
        [
            _ch("Pre-order at 2x markup", 2, {"cash": -20000, "tech": 2, "execution": 1}, "GPUs secured. Your competitors are still waiting."),
            _ch("Optimize for smaller models", 2, {"tech": 2, "innovation": 2, "product": -1}, "Your distilled model runs 10x cheaper. Customers love it."),
            _ch("Use cloud GPU on-demand", 1, {"burn_rate": 3000, "tech": 1}, "Flexible but expensive. Cloud bills are unpredictable."),
        ]),

    _ev("AI-002", "AI Ethics Controversy",
        "A researcher publishes a paper showing bias in your model's outputs. Twitter is not happy.",
        "brand", "AI", "late",
        [
            _ch("Transparency report + bias audit", 2, {"brand": 3, "tech": 1, "cash": -5000, "innovation": 1}, "Your response becomes a case study in responsible AI."),
            _ch("Quick blog post addressing concerns", 1, {"brand": 1}, "Minimally effective. The issue simmers."),
            _ch("No comment — let it blow over", 0, {"brand": -3, "growth": -1}, "It doesn't blow over. Enterprise clients start asking questions."),
        ]),

    _ev("AI-003", "OpenAI Releases Competing Model",
        "OpenAI just dropped a model that does 80% of what yours does. For free.",
        "product", "AI", "late",
        [
            _ch("Pivot to enterprise — custom fine-tuning", 2, {"product": 2, "finance": 2, "revenue": 8000}, "Enterprise loves customization. You own the niche."),
            _ch("Go open-source — build community moat", 2, {"growth": 3, "brand": 2, "innovation": 1, "revenue": -5000}, "Developers flock to you. Revenue drops but mindshare soars."),
            _ch("Double down on speed — our model is faster", 1, {"tech": 2, "product": 1}, "Benchmarks show you're 3x faster. Some customers care."),
        ]),

    _ev("AI-004", "Research Breakthrough",
        "Your ML team discovers a novel architecture that reduces inference cost by 40%.",
        "tech", "AI", "early",
        [
            _ch("Patent it and productize immediately", 2, {"tech": 3, "innovation": 3, "product": 1, "valuation_mult": 1.15}, "The patent filing makes waves. VCs come calling."),
            _ch("Publish the paper — build credibility", 2, {"brand": 2, "innovation": 2, "tech": 1}, "The paper gets 500 citations. Your team is rockstars."),
            _ch("Keep it internal — competitive advantage", 1, {"tech": 2, "execution": 1}, "Quiet edge. Competitors won't know for months."),
        ]),
]

FINTECH_EVENTS: List[Dict[str, Any]] = [
    _ev("FIN-001", "Banking Partner Due Diligence",
        "A tier-1 bank wants to integrate your API but requires a 3-month security audit first.",
        "ops", "Fintech", "early",
        [
            _ch("Full audit — hire external security firm", 2, {"cash": -15000, "ops": 2, "finance": 2, "brand": 1}, "Audit passed. The bank signs. Revenue incoming."),
            _ch("Internal audit — save money", 1, {"ops": 1, "tech": 1, "cash": -3000}, "Partial pass. Bank asks for more work."),
            _ch("Decline — too early for enterprise banking", 0, {"execution": 1}, "You stay nimble. But the opportunity doesn't come back."),
        ]),

    _ev("FIN-002", "New Regulation Announced",
        "The SEC announces new compliance rules for fintech startups. You have 90 days to comply.",
        "ops", "Fintech", "late",
        [
            _ch("Hire a compliance officer", 2, {"ops": 3, "finance": 1, "burn_rate": 4000}, "Fully compliant ahead of deadline. Competitors scramble."),
            _ch("Use compliance-as-a-service vendor", 1, {"ops": 1, "cash": -5000}, "Compliant but dependent on a third party."),
            _ch("Lobby for an extension", 1, {"brand": -1, "ops": -1}, "Extension denied. You're now behind."),
        ]),

    _ev("FIN-003", "Fraud Ring Detected",
        "Your fraud detection catches a pattern: $200K in suspicious transactions in the last 48 hours.",
        "tech", "Fintech", "late",
        [
            _ch("Freeze accounts + full investigation", 2, {"tech": 2, "ops": 2, "brand": 1, "revenue": -5000}, "Fraud contained. You publish a security advisory."),
            _ch("Flag and monitor — don't freeze yet", 1, {"tech": 1, "ops": -1}, "Some fraud slips through. Chargebacks hurt."),
            _ch("Report to authorities only", 0, {"ops": -2, "brand": -1}, "Slow response. Some customers lose money."),
        ]),

    _ev("FIN-004", "Crypto Integration Request",
        "Your biggest enterprise client wants crypto payment support. Your team has zero blockchain experience.",
        "product", "Fintech", "early",
        [
            _ch("Build crypto module — hire blockchain dev", 2, {"tech": 2, "product": 2, "burn_rate": 5000, "revenue": 10000}, "Crypto payments go live. Client is thrilled."),
            _ch("Partner with a crypto payment gateway", 1, {"product": 1, "ops": 1, "revenue": 5000}, "Quick integration. You take a revenue cut."),
            _ch("Decline — crypto isn't our focus", 0, {"execution": 1, "revenue": -3000}, "Client is disappointed. They may look elsewhere."),
        ]),
]

SAAS_EVENTS: List[Dict[str, Any]] = [
    _ev("SAAS-001", "Enterprise Client Wants Custom Features",
        "A Fortune 500 company will pay $100K/year but wants 5 custom features built.",
        "product", "SaaS", "late",
        [
            _ch("Build them all — land the whale", 2, {"product": -1, "finance": 3, "revenue": 25000, "execution": -1}, "Contract signed! But your roadmap is now hostage to one client."),
            _ch("Build 2, push 3 to roadmap", 1, {"product": 1, "finance": 2, "revenue": 15000}, "Compromise works. They sign a smaller deal."),
            _ch("Decline — stay product-led", 1, {"product": 2, "execution": 1}, "Your product stays clean. But that was a big check."),
        ]),

    _ev("SAAS-002", "Churn Spike",
        "Monthly churn just hit 8%. Customer interviews reveal onboarding is too confusing.",
        "product", "SaaS", "early",
        [
            _ch("Complete onboarding redesign", 2, {"product": 3, "growth": 1, "execution": -1}, "Churn drops to 3%. Best investment you've made."),
            _ch("Add in-app tutorials", 1, {"product": 1, "tech": 1}, "Churn drops to 6%. Improvement, not transformation."),
            _ch("Offer discounts to at-risk users", 1, {"revenue": -3000, "growth": 1}, "Buys time but doesn't fix the root cause."),
        ]),

    _ev("SAAS-003", "API Platform Launch",
        "Your devs want to open your product as an API platform. It could attract developers but needs investment.",
        "tech", "SaaS", "late",
        [
            _ch("Full API platform with developer portal", 2, {"tech": 3, "growth": 2, "innovation": 2, "cash": -10000}, "Developers build 20 integrations in month one. Ecosystem forming."),
            _ch("Limited API — key endpoints only", 1, {"tech": 1, "growth": 1, "cash": -3000}, "A few integrations trickle in. Promising."),
            _ch("Stay closed — our product, our rules", 0, {"execution": 1, "innovation": -1}, "Control maintained. Innovation opportunity missed."),
        ]),

    _ev("SAAS-004", "Pricing Tier Optimization",
        "Data shows 40% of users are on the free plan and never convert. Time to rethink pricing.",
        "finance", "SaaS", "early",
        [
            _ch("Aggressive paywall — limit free tier heavily", 2, {"finance": 3, "revenue": 8000, "growth": -2}, "Conversion jumps 5x. But free users are angry on Reddit."),
            _ch("Add a mid-tier plan with new features", 1, {"finance": 1, "product": 1, "revenue": 4000}, "New tier converts well. Smooth transition."),
            _ch("Keep free tier generous — growth first", 0, {"growth": 2, "brand": 1}, "User count grows. Revenue stays flat."),
        ]),
]

HEALTHTECH_EVENTS: List[Dict[str, Any]] = [
    _ev("HT-001", "FDA Regulatory Pathway",
        "Your health product may need FDA clearance. The legal opinion is unclear.",
        "ops", "Healthtech", "early",
        [
            _ch("Pursue FDA 510(k) clearance proactively", 2, {"ops": 3, "brand": 2, "cash": -20000, "finance": 1}, "Clearance granted! You can now sell to hospitals."),
            _ch("Classify as wellness — avoid FDA", 1, {"ops": 1, "brand": -1, "growth": 1}, "Technically legal. But hospitals won't touch you."),
            _ch("Get a formal legal opinion first", 1, {"cash": -5000, "ops": 1}, "Lawyer says you're borderline. Decision deferred."),
        ]),

    _ev("HT-002", "Hospital Pilot Program",
        "A major hospital system offers a 90-day pilot. Success could mean a $500K contract.",
        "growth", "Healthtech", "late",
        [
            _ch("All-in — dedicate a team to the pilot", 2, {"growth": 3, "product": 1, "cash": -8000, "revenue": 20000}, "Pilot succeeds. They want to roll out system-wide."),
            _ch("Run pilot with existing resources", 1, {"growth": 1, "product": 1}, "Pilot shows promise but needs more features."),
            _ch("Decline — we need product-market fit first", 0, {"execution": 1}, "You lose the opportunity. PMF work continues."),
        ]),

    _ev("HT-003", "Patient Data Privacy Incident",
        "An employee accidentally emails patient data to the wrong recipient. HIPAA implications.",
        "ops", "Healthtech", "late",
        [
            _ch("Immediate breach protocol + notification", 2, {"ops": 2, "brand": 1, "cash": -10000}, "Handled by the book. No fines. Trust maintained."),
            _ch("Internal investigation — assess scope", 1, {"ops": 1, "cash": -3000}, "Scope is minimal. You dodge a bullet."),
            _ch("Hope nobody notices", 0, {"brand": -3, "ops": -2, "cash": -25000}, "They notice. HHS investigation opens. Expensive."),
        ]),

    _ev("HT-004", "Clinical Study Opportunity",
        "A university offers to run a clinical study validating your product. Results in 6 months.",
        "innovation", "Healthtech", "early",
        [
            _ch("Fund the study — $30K investment", 2, {"cash": -30000, "innovation": 3, "brand": 2, "valuation_mult": 1.2}, "Study shows 40% improvement. Published in a peer-reviewed journal."),
            _ch("Provide product only — university pays", 1, {"innovation": 1, "brand": 1}, "Study happens slowly. Results are promising but underpowered."),
            _ch("Decline — we can't wait 6 months", 0, {"execution": 1}, "You ship faster. But no clinical validation."),
        ]),
]

ECOMMERCE_EVENTS: List[Dict[str, Any]] = [
    _ev("EC-001", "Supply Chain Disruption",
        "Your main supplier just doubled lead times. Holiday season is 2 months away.",
        "ops", "E-commerce", "late",
        [
            _ch("Find backup supplier — pay premium", 2, {"ops": 2, "cash": -12000, "execution": 1}, "New supplier delivers. Holiday stock secured."),
            _ch("Pre-order extra inventory now", 2, {"cash": -8000, "ops": 1, "finance": -1}, "Inventory risk. Some items may not sell."),
            _ch("Sell what you have — manage expectations", 1, {"ops": -1, "brand": -1, "revenue": -5000}, "Stockouts during peak season. Customers are annoyed."),
        ]),

    _ev("EC-002", "Marketplace vs Direct",
        "Amazon wants you on their marketplace. Great reach, but they take 30% and own the customer relationship.",
        "growth", "E-commerce", "early",
        [
            _ch("Join Amazon — maximize reach", 2, {"growth": 3, "revenue": 10000, "brand": -1, "finance": -1}, "Sales explode. But you're dependent on Amazon now."),
            _ch("Dual channel — Amazon + own store", 1, {"growth": 2, "ops": -1, "revenue": 5000}, "Both channels active. Logistics complexity increases."),
            _ch("Stay direct — own the relationship", 1, {"brand": 2, "growth": -1, "execution": 1}, "Slower growth but higher margins and brand control."),
        ]),

    _ev("EC-003", "Influencer Partnership",
        "A TikTok influencer with 2M followers wants to promote your product for $10K + commission.",
        "brand", "E-commerce", "early",
        [
            _ch("Full campaign — $10K + 15% commission", 2, {"brand": 3, "growth": 3, "cash": -10000, "revenue": 15000, "traction_users": 5000}, "The video goes viral. Best ROI you've ever seen."),
            _ch("Commission only — no upfront fee", 1, {"brand": 1, "growth": 1, "revenue": 3000}, "They agree but put minimal effort in."),
            _ch("Decline — build organic brand", 0, {"brand": 1}, "Slower but more sustainable brand building."),
        ]),

    _ev("EC-004", "Returns Policy Overhaul",
        "Return rate is 15%. Free returns are killing margins, but customers expect it.",
        "finance", "E-commerce", "late",
        [
            _ch("Keep free returns — invest in quality control", 2, {"ops": 2, "product": 1, "cash": -6000, "brand": 1}, "Return rate drops to 8% through better QC. Win-win."),
            _ch("Charge for returns — protect margins", 1, {"finance": 2, "revenue": 5000, "brand": -2, "growth": -1}, "Margins improve but customer satisfaction drops."),
            _ch("Free returns for premium tier only", 1, {"finance": 1, "brand": 1, "revenue": 3000}, "Smart segmentation. Premium users love it."),
        ]),
]


# ═══════════════════════════════════════════════════════════════════
# SHOCK EVENTS (triggered by market shocks)
# ═══════════════════════════════════════════════════════════════════

SHOCK_EVENTS: List[Dict[str, Any]] = [
    _ev("SHOCK-001", "Market Crash — Emergency Board Meeting",
        "Markets are in free-fall. Your investors demand an emergency plan to extend runway.",
        "finance", None, "late",
        [
            _ch("Cut 30% of costs immediately", 2, {"burn_rate": -8000, "ops": -2, "execution": -1, "cash": 5000}, "Painful layoffs. But runway extends by 6 months."),
            _ch("Raise an emergency bridge round", 2, {"cash": 50000, "equity": 5.0, "finance": 1}, "Money secured at terrible terms. Dilution hurts."),
            _ch("Do nothing — this will pass", 0, {"finance": -2, "execution": -1}, "Investors are furious. Board seat threatened."),
        ], is_shock=True),

    _ev("SHOCK-002", "AI Regulation Bombshell",
        "The EU announces sweeping AI regulation. Compliance deadline: 6 months.",
        "ops", None, "late",
        [
            _ch("Fast-track compliance team", 2, {"ops": 2, "cash": -15000, "burn_rate": 3000, "brand": 1}, "Compliant before competitors. First-mover advantage."),
            _ch("Wait for clarity — lobby for exemptions", 1, {"ops": -1, "brand": -1}, "Exemption denied. You're now behind."),
            _ch("Pivot to non-regulated use cases", 2, {"product": 1, "innovation": 1, "revenue": -5000}, "Safe but limiting. Some customers leave."),
        ], is_shock=True),

    _ev("SHOCK-003", "Talent Exodus",
        "Three competitors just raised massive rounds and are poaching your employees with 2x salaries.",
        "ops", None, "early",
        [
            _ch("Counter-offer + equity refresh for key people", 2, {"burn_rate": 5000, "equity": 2.0, "ops": 2, "tech": 1}, "Retained the critical team. Burn increases."),
            _ch("Emphasize culture and mission", 1, {"brand": 1, "ops": 1}, "Some stay for the mission. Others leave anyway."),
            _ch("Let them go — hire fresh talent", 1, {"ops": -2, "tech": -1, "cash": -8000}, "Knowledge lost. New hires take months to ramp."),
        ], is_shock=True),

    _ev("SHOCK-004", "Economic Boom — Opportunity Knocks",
        "The economy is surging. Customer budgets are expanding. Time to be aggressive.",
        "growth", None, "early",
        [
            _ch("Double marketing spend", 2, {"cash": -20000, "growth": 4, "brand": 2, "traction_users": 5000}, "Growth goes parabolic. Your best quarter ever."),
            _ch("Hire aggressively", 2, {"burn_rate": 8000, "tech": 2, "ops": 1, "execution": 1}, "Team expands 40%. Capacity scales up."),
            _ch("Save for the downturn", 1, {"finance": 2, "cash": 10000}, "Cash reserves grow. You'll be glad when winter comes."),
        ], is_shock=True),

    _ev("SHOCK-005", "Pandemic-Like Disruption",
        "A global health crisis shuts down offices worldwide. Remote work becomes mandatory.",
        "ops", None, "late",
        [
            _ch("Pivot to remote-first — invest in tools", 2, {"ops": 2, "tech": 1, "burn_rate": -3000, "execution": 1}, "Your remote culture becomes a recruiting advantage."),
            _ch("Temporary adjustments — wait it out", 1, {"ops": -1, "execution": -1}, "Productivity drops 30%. Team morale suffers."),
            _ch("Lay off and restructure", 2, {"burn_rate": -10000, "ops": -2, "execution": -2, "cash": 15000}, "Survival mode. You'll rebuild when it's over."),
        ], is_shock=True),

    _ev("SHOCK-006", "Currency Crash",
        "Your operating country's currency drops 20%. International revenue is now worth less locally.",
        "finance", None, "late",
        [
            _ch("Hedge currency exposure", 2, {"cash": -8000, "finance": 2, "ops": 1}, "Hedged. Future volatility won't hurt as much."),
            _ch("Switch to USD pricing", 1, {"finance": 1, "brand": -1, "revenue": 5000}, "Revenue stabilizes but local customers complain."),
            _ch("Absorb the loss", 0, {"finance": -2, "revenue": -8000}, "Margins shrink. Burn accelerates."),
        ], is_shock=True),

    _ev("SHOCK-007", "Major Customer Bankruptcy",
        "Your biggest customer (20% of revenue) just filed for bankruptcy. Payment? Not coming.",
        "finance", None, "late",
        [
            _ch("Aggressive diversification — land 5 small clients", 2, {"growth": 2, "finance": 1, "cash": -5000, "revenue": 3000}, "Revenue diversified. Never again."),
            _ch("Negotiate partial payment from bankruptcy court", 1, {"finance": 1, "cash": 8000}, "You recover 40 cents on the dollar. Better than nothing."),
            _ch("Cut costs to match new revenue reality", 1, {"burn_rate": -5000, "ops": -1}, "Painful adjustment. Runway preserved."),
        ], is_shock=True),

    _ev("SHOCK-008", "Breakthrough Technology Disruption",
        "A new technology makes your core infrastructure 10x cheaper. First mover advantage is massive.",
        "tech", None, "early",
        [
            _ch("Migrate immediately — all hands on deck", 2, {"tech": 3, "innovation": 2, "burn_rate": -5000, "execution": -1}, "Migration complete. Your cost structure is now industry-leading."),
            _ch("Gradual migration over 2 quarters", 1, {"tech": 1, "innovation": 1, "burn_rate": -2000}, "Steady progress. Competitors are also migrating."),
            _ch("Wait for it to mature", 0, {"tech": -1, "innovation": -1}, "By the time you move, everyone else already has."),
        ], is_shock=True),

    _ev("SHOCK-009", "Competitor Implodes",
        "Your biggest competitor just had a massive scandal. Their customers are looking for alternatives.",
        "growth", None, "late",
        [
            _ch("Aggressive win-back campaign", 2, {"cash": -10000, "growth": 4, "brand": 2, "revenue": 12000, "traction_users": 3000}, "You poach 30% of their customer base. Incredible quarter."),
            _ch("Reach out to their enterprise clients", 1, {"growth": 2, "finance": 1, "revenue": 6000}, "Three enterprise clients switch. Steady gains."),
            _ch("Stay quiet — don't pile on", 0, {"brand": 1}, "Classy move. Some customers find you organically."),
        ], is_shock=True),

    _ev("SHOCK-010", "Interest Rate Spike",
        "Central banks raise rates sharply. VC funding dries up. Only profitable startups survive.",
        "finance", None, "late",
        [
            _ch("Sprint to profitability", 2, {"revenue": 8000, "burn_rate": -5000, "growth": -2, "execution": 2}, "Cash-flow positive in 2 months. VCs now call YOU."),
            _ch("Extend runway — cut discretionary spend", 1, {"burn_rate": -3000, "ops": -1}, "Lean times. But you survive."),
            _ch("Raise now at any terms", 1, {"cash": 40000, "equity": 8.0, "finance": -1}, "Money secured but at a crushing valuation."),
        ], is_shock=True),
]


# ═══════════════════════════════════════════════════════════════════
# ADDITIONAL UNIVERSAL EVENTS (late game focus)
# ═══════════════════════════════════════════════════════════════════

UNIVERSAL_EVENTS_LATE: List[Dict[str, Any]] = [
    _ev("UNI-021", "Podcast Fame",
        "A major startup podcast wants you as a guest. It reaches 500K listeners.",
        "brand", None, "early",
        [
            _ch("Accept and prepare a compelling story", 2, {"brand": 3, "growth": 2, "traction_users": 2000}, "Episode drops. Your social following triples overnight."),
            _ch("Do a quick interview with minimal prep", 1, {"brand": 1, "growth": 1}, "Decent coverage. Some new inbound signups."),
            _ch("Decline — too busy building", 0, {}, "The opportunity passes. Back to work."),
        ]),

    _ev("UNI-022", "Remote Work Policy",
        "Half your team is demanding a remote-first policy. The other half wants in-office culture.",
        "ops", None, "early",
        [
            _ch("Go fully remote-first — global talent", 1, {"ops": 1, "growth": 1, "burn_rate": -3000}, "You can now hire anywhere. Team is happier."),
            _ch("Hybrid policy — best of both worlds", 1, {"ops": 1, "execution": 1}, "Most people are satisfied. Some grumbling."),
            _ch("Mandatory office — culture first", 2, {"execution": 2, "brand": 1, "burn_rate": 2000}, "Strong culture. But 2 people resign."),
        ]),

    _ev("UNI-023", "Board Observer Seat",
        "An investor wants an observer seat on your board. No voting rights, but they'll see everything.",
        "finance", None, "early",
        [
            _ch("Grant observer seat — more support", 1, {"finance": 2, "brand": 1}, "They introduce you to 3 strategic partners."),
            _ch("Negotiate limited information rights instead", 1, {"finance": 1, "ops": 1}, "A middle ground. They accept grudgingly."),
            _ch("Decline — keep governance lean", 0, {"execution": 1}, "Your board stays simple. You keep full control."),
        ]),

    _ev("UNI-024", "Y Combinator Demo Day",
        "You've been accepted to YC. Demo Day is next month. It could change everything.",
        "brand", None, "early",
        [
            _ch("All-in — pitch to 1000 investors", 2, {"brand": 3, "finance": 3, "cash": 100000, "valuation_mult": 1.3}, "You raise $500K in 48 hours. Game changer."),
            _ch("Demo Day only — no media blitz", 1, {"brand": 2, "finance": 1, "cash": 30000}, "Good connections. A couple of interested angels."),
            _ch("Skip — YC terms are too dilutive", 0, {"execution": 1}, "You keep more equity. Slower path, but yours."),
        ]),

    _ev("UNI-025", "Security Audit Required",
        "Your enterprise client says they need a SOC 2 audit before signing. It takes months.",
        "ops", None, "late",
        [
            _ch("Start SOC 2 audit immediately", 2, {"ops": 3, "brand": 2, "cash": -18000}, "Certified! Enterprise deals now flow freely."),
            _ch("Use a faster compliance tool", 1, {"ops": 1, "cash": -5000}, "Partial compliance. Client accepts it provisionally."),
            _ch("Negotiate a waiver from the client", 1, {"ops": 1}, "They grant 90 days. You're buying time."),
        ]),

    _ev("UNI-026", "Product Hunt Launch",
        "Your team wants to do a big Product Hunt launch. Top 5 could mean 10K signups.",
        "growth", None, "early",
        [
            _ch("Full launch campaign — weeks of prep", 2, {"growth": 4, "brand": 2, "traction_users": 8000, "cash": -3000}, "#1 Product of the Day! Inbound explodes."),
            _ch("Soft launch — see what happens", 1, {"growth": 2, "brand": 1, "traction_users": 2000}, "#12 for the day. Good exposure."),
            _ch("Skip — not the right time", 0, {"execution": 1}, "You wait for a stronger product before going public."),
        ]),

    _ev("UNI-027", "Key Advisor Departing",
        "Your most connected advisor is moving to a competitor. They want to bow out gracefully.",
        "brand", None, "late",
        [
            _ch("Negotiate a transition period", 1, {"brand": 1, "finance": 1}, "30-day handover. They intro you to their network."),
            _ch("Let them go — no hard feelings", 0, {"brand": 1, "execution": 1}, "Clean exit. You stay on good terms."),
            _ch("Contest the move legally", 2, {"cash": -10000, "brand": -2}, "Legal action backfires. Reputation takes a hit."),
        ]),

    _ev("UNI-028", "Sustainability Initiative",
        "A large investor is pushing for a sustainability report. It's becoming a table-stakes ask.",
        "brand", None, "late",
        [
            _ch("Full ESG report + carbon offset program", 2, {"brand": 3, "ops": 1, "cash": -8000}, "ESG score: excellent. Premium investors take notice."),
            _ch("Lightweight sustainability pledge", 1, {"brand": 2}, "Symbolic but effective for now."),
            _ch("Ignore — we have bigger problems", 0, {"brand": -1}, "The investor loses interest. Not a crisis yet."),
        ]),

    _ev("UNI-029", "CFO Resigns",
        "Your CFO just handed in their notice. Board meeting in 2 weeks. The books are a mess.",
        "finance", None, "late",
        [
            _ch("Promote internal controller as interim CFO", 1, {"finance": 1, "ops": 1}, "Smooth transition. Costs nothing extra."),
            _ch("Hire a fractional CFO immediately", 1, {"finance": 2, "cash": -6000}, "Expensive but experienced. Board is reassured."),
            _ch("Handle finances yourself temporarily", 0, {"finance": -1, "execution": -2}, "You're now the founder-CFO. Something will slip."),
        ]),

    _ev("UNI-030", "IP Portfolio Review",
        "Your lawyer recommends filing 3 patents that could protect your core technology.",
        "tech", None, "late",
        [
            _ch("File all 3 patents", 2, {"tech": 2, "innovation": 2, "cash": -15000, "valuation_mult": 1.1}, "Patents filed. Moat deepens. Acquirers take notice."),
            _ch("File the most critical one", 1, {"tech": 1, "innovation": 1, "cash": -5000}, "Core IP protected. Others can wait."),
            _ch("Skip — patents are expensive and slow", 0, {"cash": 5000}, "You save money. Competitors may copy you later."),
        ]),
]

# ═══════════════════════════════════════════════════════════════════
# ADDITIONAL AI EVENTS
# ═══════════════════════════════════════════════════════════════════

AI_EVENTS_EXTRA: List[Dict[str, Any]] = [
    _ev("AI-005", "Model Hallucination Incident",
        "Your AI assistant gave a customer dangerous advice. It's now on TechCrunch.",
        "brand", "AI", "late",
        [
            _ch("Immediate model rollback + public apology", 2, {"brand": 2, "tech": 1, "cash": -5000}, "Crisis contained. Your transparency is praised."),
            _ch("Quiet fix — patch the model silently", 1, {"tech": 1}, "Fix deployed. The article stays up but no new coverage."),
            _ch("Dispute the story — PR fight", 1, {"brand": -3, "cash": -8000}, "The PR battle makes it worse. Streisand effect."),
        ]),

    _ev("AI-006", "Foundation Model Partnership",
        "Anthropic wants to use your product as a showcase for their API. Massive visibility.",
        "brand", "AI", "late",
        [
            _ch("Co-marketing deal + case study", 2, {"brand": 4, "growth": 3, "innovation": 2}, "Featured on Anthropic's website. Signups triple."),
            _ch("Technical partnership only", 1, {"tech": 2, "innovation": 1}, "Solid tech collab. No public announcement."),
            _ch("Decline — stay vendor-neutral", 0, {"execution": 1, "innovation": 1}, "You avoid lock-in. Good long-term positioning."),
        ]),

    _ev("AI-007", "AI Safety Researcher Joins",
        "A Stanford AI safety researcher wants to join your team part-time. They have concerns.",
        "tech", "AI", "early",
        [
            _ch("Hire them full-time — safety is our priority", 2, {"tech": 2, "brand": 2, "innovation": 1, "burn_rate": 5000}, "Safety-first reputation becomes a selling point."),
            _ch("Part-time advisor role", 1, {"tech": 1, "brand": 1}, "Good optics. Limited integration."),
            _ch("Decline — too many cooks", 0, {"execution": 1}, "You stay lean. Safety concerns go unaddressed."),
        ]),

    _ev("AI-008", "Benchmarking Report",
        "An independent researcher publishes a benchmark where your model ranks #3. Your team is devastated.",
        "product", "AI", "late",
        [
            _ch("Major model improvement sprint", 2, {"tech": 3, "product": 2, "innovation": 2, "execution": -1}, "Next benchmark: you're #1. The narrative flips."),
            _ch("Highlight your unique strengths", 1, {"brand": 2, "product": 1}, "You reframe the narrative. Customers who matter stay."),
            _ch("Ignore it — benchmarks don't matter", 0, {"execution": 1, "brand": -1}, "Sales team struggles to answer client questions."),
        ]),

    _ev("AI-009", "Inference Cost Optimization",
        "Your cloud bills are eating 40% of revenue. There's a way to cut them in half with effort.",
        "tech", "AI", "early",
        [
            _ch("Full optimization project — 6-week sprint", 2, {"tech": 3, "finance": 2, "burn_rate": -8000}, "Cloud costs cut 55%. Margin improvement is massive."),
            _ch("Incremental optimizations", 1, {"tech": 1, "finance": 1, "burn_rate": -3000}, "10% savings. Better than nothing."),
            _ch("Raise prices instead", 1, {"finance": 1, "revenue": 5000, "growth": -1}, "Margins improve but some customers churn."),
        ]),

    _ev("AI-010", "Data Licensing Deal",
        "A hedge fund wants to license your proprietary training dataset for $200K/year.",
        "finance", "AI", "late",
        [
            _ch("License it — pure profit", 1, {"finance": 2, "revenue": 16000}, "Non-dilutive revenue stream. Board loves it."),
            _ch("Negotiate exclusive terms with premium price", 2, {"finance": 3, "revenue": 25000, "brand": -1}, "Exclusive deal at $300K. Your data stays proprietary."),
            _ch("Decline — data is our moat", 0, {"tech": 1, "innovation": 1}, "Data stays yours. Competitors can't replicate it."),
        ]),
]

# ═══════════════════════════════════════════════════════════════════
# ADDITIONAL FINTECH EVENTS
# ═══════════════════════════════════════════════════════════════════

FINTECH_EVENTS_EXTRA: List[Dict[str, Any]] = [
    _ev("FIN-005", "Central Bank Digital Currency",
        "Your country's central bank announces a CBDC trial. Your payment rails could be obsolete.",
        "tech", "Fintech", "late",
        [
            _ch("Pivot to CBDC integration partner", 2, {"tech": 2, "innovation": 3, "ops": 1}, "First-mover in CBDC ecosystem. Huge opportunity."),
            _ch("Wait and watch — too early to tell", 0, {"execution": 1}, "You monitor. No action yet."),
            _ch("Double down on private payment rails", 1, {"tech": 1, "execution": 2}, "Bet on private sector. CBDC may not take off."),
        ]),

    _ev("FIN-006", "Buy Now Pay Later Feature",
        "Your analytics show BNPL could increase average transaction value by 30%.",
        "product", "Fintech", "early",
        [
            _ch("Build native BNPL — own the full stack", 2, {"product": 3, "tech": 2, "revenue": 8000, "burn_rate": 3000}, "BNPL live. Transaction values jump 35%."),
            _ch("Partner with Affirm or Klarna", 1, {"product": 2, "revenue": 4000}, "Fast to market. You take a revenue cut."),
            _ch("Not now — regulatory complexity", 0, {"ops": 1}, "Safer. But competitors may move first."),
        ]),

    _ev("FIN-007", "Stablecoin Treasury Management",
        "Your CFO suggests holding 10% of treasury in USDC for yield. Risk vs. return debate.",
        "finance", "Fintech", "late",
        [
            _ch("Allocate 10% to USDC — 5% APY", 1, {"finance": 2, "cash": 8000}, "Yield earned. Board is divided but accepts it."),
            _ch("Keep everything in fiat — safety first", 0, {"finance": 1}, "Conservative. No surprises."),
            _ch("Go bigger — 25% in crypto", 2, {"finance": -1, "cash": -10000}, "Crypto dumps 20%. Lesson learned."),
        ]),

    _ev("FIN-008", "IPO Readiness Assessment",
        "Your investment bankers say you could be IPO-ready in 18 months. The prep is expensive.",
        "finance", "Fintech", "late",
        [
            _ch("Start IPO preparation now", 2, {"finance": 3, "ops": 2, "cash": -25000, "valuation_mult": 1.2}, "You're on the IPO track. Valuation premium kicks in."),
            _ch("Dual-track: IPO + M&A process", 1, {"finance": 2, "ops": 1}, "Optionality maximized. Resource intensive."),
            _ch("Too early — focus on fundamentals", 0, {"execution": 2, "finance": 1}, "Smart. Most startups that rush IPOs regret it."),
        ]),
]

# ═══════════════════════════════════════════════════════════════════
# ADDITIONAL SAAS EVENTS
# ═══════════════════════════════════════════════════════════════════

SAAS_EVENTS_EXTRA: List[Dict[str, Any]] = [
    _ev("SAAS-005", "Annual Recurring Revenue Milestone",
        "You've hit $1M ARR. The board wants a party. The team wants headcount.",
        "finance", "SaaS", "late",
        [
            _ch("Celebrate + hire 5 sales reps", 2, {"growth": 3, "burn_rate": 15000, "revenue": 12000}, "Sales team drives next ARR milestone fast."),
            _ch("Reinvest in product + engineering", 2, {"product": 2, "tech": 2, "execution": 1}, "Product gets better. Churn drops. NRR climbs."),
            _ch("Stay lean — bank the milestone", 0, {"finance": 2, "execution": 1}, "Conservative. Runway extends. VCs applaud."),
        ]),

    _ev("SAAS-006", "Customer Success Program",
        "Your churn is tied to poor onboarding. A CS program could fix it.",
        "ops", "SaaS", "early",
        [
            _ch("Build a dedicated CS team", 2, {"ops": 3, "revenue": 6000, "burn_rate": 4000}, "NPS jumps from 32 to 58. Logo churn drops."),
            _ch("Create self-serve success resources", 1, {"product": 2, "ops": 1}, "Good documentation reduces support tickets 40%."),
            _ch("Let customers figure it out", 0, {"finance": 1, "ops": -1}, "Churn stays high. You're losing revenue silently."),
        ]),

    _ev("SAAS-007", "Competitive Feature Parity Race",
        "Salesforce just bought a startup that does what you do. Game on.",
        "product", "SaaS", "late",
        [
            _ch("Focus on niche — own a vertical", 2, {"product": 2, "brand": 2, "growth": 2}, "You dominate the vertical Salesforce ignores."),
            _ch("Match their feature set — sprint mode", 2, {"tech": 2, "product": 1, "execution": -2}, "Feature parity reached. But tech debt is brutal."),
            _ch("Partner with Salesforce — if you can't beat them", 1, {"revenue": 10000, "growth": 1, "execution": 1}, "Marketplace listing drives new pipeline."),
        ]),

    _ev("SAAS-008", "White-Label Request",
        "An agency wants to resell your software under their brand. 200 clients, $50K upfront.",
        "growth", "SaaS", "late",
        [
            _ch("Accept — white-label partner program", 2, {"revenue": 15000, "growth": 2, "brand": -1}, "Revenue channel opened. Brand gets diluted slightly."),
            _ch("Co-branded deal instead", 1, {"revenue": 8000, "brand": 1, "growth": 1}, "Both brands visible. Agency accepts. Good deal."),
            _ch("Decline — brand is everything", 0, {"brand": 2}, "You protect the brand. Slower growth."),
        ]),
]

# ═══════════════════════════════════════════════════════════════════
# ADDITIONAL HEALTHTECH EVENTS
# ═══════════════════════════════════════════════════════════════════

HEALTHTECH_EVENTS_EXTRA: List[Dict[str, Any]] = [
    _ev("HT-005", "Telemedicine Integration",
        "A major telemedicine platform wants to embed your diagnostic tool in their app.",
        "growth", "Healthtech", "late",
        [
            _ch("Full integration + API partnership", 2, {"growth": 3, "tech": 2, "revenue": 12000, "traction_users": 5000}, "Millions of patients now see your tool. Massive distribution."),
            _ch("Pilot with 10K users first", 1, {"growth": 1, "tech": 1, "revenue": 3000}, "Steady. Data is promising."),
            _ch("Decline — need more clinical validation", 0, {"innovation": 1, "ops": 1}, "Responsible choice. Clinical evidence strengthens."),
        ]),

    _ev("HT-006", "Insurance Reimbursement Win",
        "A major insurer agrees to reimburse patients for your digital health tool.",
        "finance", "Healthtech", "late",
        [
            _ch("Negotiate direct B2B with insurers", 2, {"finance": 3, "revenue": 20000, "ops": 2}, "Direct insurer contracts. Revenue triples."),
            _ch("Patient-paid model stays primary", 0, {"finance": 1, "growth": -1}, "Simpler. But massive market left on table."),
            _ch("Partner with a pharmacy chain for distribution", 1, {"growth": 2, "revenue": 8000}, "Distribution deal. Pharmacies push the product."),
        ]),

    _ev("HT-007", "Wearable Data Integration",
        "Apple and Fitbit want to integrate your app with their health platforms.",
        "tech", "Healthtech", "early",
        [
            _ch("Full integration with both platforms", 2, {"tech": 3, "growth": 3, "traction_users": 10000}, "10M potential users in reach. Distribution explodes."),
            _ch("Apple only — premium segment focus", 1, {"tech": 2, "brand": 1, "traction_users": 5000}, "Premium positioning. iOS-first strategy pays off."),
            _ch("Build our own wearable integration", 2, {"tech": 2, "innovation": 2, "cash": -15000}, "Independent stack. No platform risk."),
        ]),

    _ev("HT-008", "Genomics Partnership",
        "A genomics company wants to co-develop a personalized medicine feature.",
        "innovation", "Healthtech", "late",
        [
            _ch("Joint product development", 2, {"innovation": 4, "tech": 2, "cash": -10000, "valuation_mult": 1.15}, "Personalized medicine feature gets serious press."),
            _ch("Data sharing agreement only", 1, {"innovation": 2, "tech": 1}, "Incremental. Interesting research collaboration."),
            _ch("Decline — too early for genomics", 0, {"execution": 1}, "Focus maintained. Genomics can wait."),
        ]),
]

# ═══════════════════════════════════════════════════════════════════
# ADDITIONAL E-COMMERCE EVENTS
# ═══════════════════════════════════════════════════════════════════

ECOMMERCE_EVENTS_EXTRA: List[Dict[str, Any]] = [
    _ev("EC-005", "Black Friday Crunch",
        "Black Friday is 3 weeks away. Your servers handled 500 concurrent users. You'll need 50,000.",
        "tech", "E-commerce", "late",
        [
            _ch("Full infrastructure scale-up now", 2, {"tech": 3, "ops": 2, "cash": -12000}, "Flawless Black Friday. Best revenue day ever."),
            _ch("Use auto-scaling cloud setup", 1, {"tech": 1, "ops": 1, "cash": -4000}, "Some slowdowns but no crashes. Revenue pours in."),
            _ch("Hope for the best", 0, {"tech": -2, "brand": -2}, "Site crashes for 4 hours. $50K in lost sales."),
        ]),

    _ev("EC-006", "Own-Brand Product Launch",
        "Your margin analysis shows private label products could boost margin by 40%.",
        "product", "E-commerce", "late",
        [
            _ch("Launch 3 private label products", 2, {"product": 2, "finance": 2, "revenue": 10000, "cash": -20000}, "Own-brand products crush. 60% gross margin."),
            _ch("Test with 1 product first", 1, {"product": 1, "finance": 1, "cash": -8000}, "Pilot works. Proof of concept ready."),
            _ch("Stick to marketplace model — lower risk", 0, {"ops": 1, "execution": 1}, "Safe. You avoid inventory risk."),
        ]),

    _ev("EC-007", "Customer Loyalty Program",
        "Your repeat purchase rate is 15%. Industry average is 40%. Something is wrong.",
        "growth", "E-commerce", "early",
        [
            _ch("Full loyalty program — points, tiers, perks", 2, {"growth": 3, "brand": 2, "revenue": 8000, "burn_rate": 2000}, "Repeat rate jumps to 35% in 6 weeks."),
            _ch("Simple referral program", 1, {"growth": 2, "brand": 1, "traction_users": 1000}, "Referrals drive 15% of new signups."),
            _ch("Fix product quality instead", 2, {"product": 2, "ops": 1, "execution": 1}, "Root cause addressed. Retention improves organically."),
        ]),

    _ev("EC-008", "Same-Day Delivery War",
        "Amazon just launched same-day delivery in your market. Customers are asking why you can't.",
        "ops", "E-commerce", "late",
        [
            _ch("Partner with a last-mile logistics startup", 2, {"ops": 3, "brand": 2, "revenue": 6000, "burn_rate": 3000}, "Same-day live. Conversion rate lifts 12%."),
            _ch("2-hour delivery in key cities only", 1, {"ops": 1, "brand": 1}, "Partial solution. Urban customers are happy."),
            _ch("Compete on curation, not speed", 1, {"brand": 2, "product": 1}, "You position as premium, not fast. Different market."),
        ]),
]

# ═══════════════════════════════════════════════════════════════════
# MASTER EVENT LIST + HELPERS
# ═══════════════════════════════════════════════════════════════════

ALL_EVENTS: List[Dict[str, Any]] = (
    UNIVERSAL_EVENTS
    + UNIVERSAL_EVENTS_LATE
    + AI_EVENTS
    + AI_EVENTS_EXTRA
    + FINTECH_EVENTS
    + FINTECH_EVENTS_EXTRA
    + SAAS_EVENTS
    + SAAS_EVENTS_EXTRA
    + HEALTHTECH_EVENTS
    + HEALTHTECH_EVENTS_EXTRA
    + ECOMMERCE_EVENTS
    + ECOMMERCE_EVENTS_EXTRA
    + SHOCK_EVENTS
)

SECTOR_EVENT_MAP: Dict[str, List[Dict[str, Any]]] = {
    "AI": AI_EVENTS + AI_EVENTS_EXTRA,
    "Fintech": FINTECH_EVENTS + FINTECH_EVENTS_EXTRA,
    "SaaS": SAAS_EVENTS + SAAS_EVENTS_EXTRA,
    "Healthtech": HEALTHTECH_EVENTS + HEALTHTECH_EVENTS_EXTRA,
    "E-commerce": ECOMMERCE_EVENTS + ECOMMERCE_EVENTS_EXTRA,
}

ALL_UNIVERSAL_EVENTS = UNIVERSAL_EVENTS + UNIVERSAL_EVENTS_LATE


def get_events_for_sector(sector: str) -> List[Dict[str, Any]]:
    """Return universal + sector-specific events (excluding shocks)."""
    sector_events = SECTOR_EVENT_MAP.get(sector, [])
    return ALL_UNIVERSAL_EVENTS + sector_events


def get_shock_events() -> List[Dict[str, Any]]:
    """Return all shock events."""
    return SHOCK_EVENTS


def get_event_by_id(event_id: str) -> Dict[str, Any] | None:
    """Look up any event by ID."""
    for ev in ALL_EVENTS:
        if ev["id"] == event_id:
            return ev
    return None
