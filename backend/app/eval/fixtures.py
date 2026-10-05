"""Synthetic demo corpus used for the eval harness and for local demoing.

All text below is original boilerplate written for this project -- not
copied from any real contract or case -- since CourtListener's API now
requires an authenticated token (see app/ingestion/courtlistener.py) that
this environment doesn't have. Swap in real CourtListener opinions once a
token is available; the ingestion pipeline doesn't change.

Each CONTRACT/CASE is a list of (heading, body) pairs rendered as a DOCX
with the heading as its own paragraph (so the existing heading-based
chunker in app/ingestion/chunking.py splits on it) followed by the body
paragraph. GOLD_QA items reference these by filename + a short substring
that must appear in the correct chunk, so eval and seeding share one
source of truth.
"""

from dataclasses import dataclass

CONTRACTS: dict[str, list[tuple[str, str]]] = {
    "master_services_agreement.docx": [
        (
            "1. Indemnification",
            "The Service Provider shall indemnify, defend, and hold harmless the Client from and against any "
            "third-party claims arising out of the Service Provider's breach of this Agreement, except to the "
            "extent such claims arise from the Client's own gross negligence or willful misconduct.",
        ),
        (
            "2. Limitation of Liability",
            "Neither party's aggregate liability under this Agreement shall exceed the total fees paid in the "
            "twelve months preceding the claim, and neither party shall be liable for consequential, incidental, "
            "or punitive damages.",
        ),
        (
            "3. Confidentiality",
            "Each party shall hold the other's Confidential Information in strict confidence and shall not "
            "disclose it to any third party without prior written consent, except as required by law.",
        ),
        (
            "4. Termination",
            "Either party may terminate this Agreement upon thirty days' written notice if the other party "
            "materially breaches this Agreement and fails to cure such breach within fifteen days of notice.",
        ),
        (
            "5. Governing Law",
            "This Agreement shall be governed by and construed in accordance with the laws of the State of "
            "New York, without regard to its conflict of laws principles.",
        ),
    ],
    "employment_agreement.docx": [
        (
            "1. Non-Competition",
            "During employment and for twelve months thereafter, Employee shall not engage in any business that "
            "directly competes with the Company within the geographic territory where the Company actively "
            "conducts business.",
        ),
        (
            "2. Severance",
            "If Employee is terminated without Cause, the Company shall pay Employee severance equal to three "
            "months of base salary, payable in a lump sum within thirty days of termination.",
        ),
        (
            "3. Intellectual Property Assignment",
            "Employee hereby assigns to the Company all right, title, and interest in any invention, work of "
            "authorship, or trade secret conceived during employment and related to the Company's business.",
        ),
        (
            "4. At-Will Employment",
            "Employment under this Agreement is at-will, meaning either party may terminate the employment "
            "relationship at any time, with or without cause, subject to the notice provisions herein.",
        ),
        (
            "5. Dispute Resolution",
            "Any dispute arising out of this Agreement shall be resolved by binding arbitration administered "
            "under the rules of the American Arbitration Association, with the arbitration seated in Delaware.",
        ),
    ],
    "commercial_lease.docx": [
        (
            "1. Rent Escalation",
            "Base rent shall increase by three percent annually on each anniversary of the Commencement Date, "
            "compounded, and shall be payable in advance on the first day of each month.",
        ),
        (
            "2. Maintenance Obligations",
            "Tenant shall be responsible for routine maintenance and repair of the interior of the Premises, "
            "while Landlord shall maintain the structural elements, roof, and building systems.",
        ),
        (
            "3. Assignment and Subletting",
            "Tenant shall not assign this Lease or sublet the Premises, in whole or in part, without Landlord's "
            "prior written consent, which shall not be unreasonably withheld.",
        ),
        (
            "4. Default and Remedies",
            "If Tenant fails to pay rent within ten days of the due date, Landlord may, after written notice, "
            "declare a default and pursue all remedies available at law, including termination of this Lease.",
        ),
        (
            "5. Insurance Requirements",
            "Tenant shall maintain commercial general liability insurance with limits of not less than two "
            "million dollars per occurrence and shall name Landlord as an additional insured.",
        ),
    ],
    "software_license_agreement.docx": [
        (
            "1. License Grant",
            "Licensor grants Licensee a non-exclusive, non-transferable license to use the Software solely for "
            "Licensee's internal business purposes, limited to the number of licensed seats purchased.",
        ),
        (
            "2. Warranty Disclaimer",
            "Except as expressly stated herein, the Software is provided 'as is' without warranty of any kind, "
            "and Licensor disclaims all implied warranties of merchantability and fitness for a particular purpose.",
        ),
        (
            "3. Support and Maintenance",
            "Licensor shall provide bug-fix support and maintenance releases for twelve months following "
            "delivery, after which continued support requires a separate maintenance agreement.",
        ),
        (
            "4. Audit Rights",
            "Licensor may, upon fifteen days' notice and no more than once per year, audit Licensee's use of the "
            "Software to confirm compliance with the licensed seat count.",
        ),
        (
            "5. Export Control",
            "Licensee shall not export or re-export the Software in violation of applicable export control laws "
            "and regulations, including those of the United States.",
        ),
    ],
    "merger_agreement.docx": [
        (
            "1. Representations and Warranties",
            "The Target represents and warrants that its financial statements fairly present its financial "
            "condition in all material respects and that it has disclosed all material contracts to the Acquirer.",
        ),
        (
            "2. Closing Conditions",
            "The obligations of the parties to close the transaction are conditioned upon receipt of all required "
            "regulatory approvals and the absence of any injunction prohibiting the merger.",
        ),
        (
            "3. Indemnification Escrow",
            "Ten percent of the purchase price shall be held in escrow for eighteen months to satisfy any "
            "indemnification claims arising from a breach of the Target's representations and warranties.",
        ),
        (
            "4. Material Adverse Effect",
            "Acquirer may terminate this Agreement if a Material Adverse Effect occurs with respect to the "
            "Target's business, operations, or financial condition between signing and closing.",
        ),
        (
            "5. Termination Fee",
            "If the Target terminates this Agreement to accept a superior proposal, the Target shall pay the "
            "Acquirer a termination fee equal to three percent of the transaction value.",
        ),
    ],
    "mutual_nda.docx": [
        (
            "1. Definition of Confidential Information",
            "Confidential Information means any non-public technical, business, or financial information "
            "disclosed by either party that is marked confidential or that would reasonably be understood to be "
            "confidential given the nature of the information.",
        ),
        (
            "2. Exclusions from Confidentiality",
            "Confidential Information does not include information that is independently developed by the "
            "receiving party, becomes publicly available through no fault of the receiving party, or was already "
            "known to the receiving party prior to disclosure.",
        ),
        (
            "3. Term and Survival",
            "The confidentiality obligations under this Agreement shall survive for five years following "
            "disclosure, except for trade secrets, which shall remain protected for as long as they qualify as "
            "trade secrets under applicable law.",
        ),
        (
            "4. Remedies for Breach",
            "The parties acknowledge that unauthorized disclosure may cause irreparable harm for which monetary "
            "damages are an inadequate remedy, and the disclosing party may seek injunctive relief in addition "
            "to any other remedies available.",
        ),
        (
            "5. Return of Materials",
            "Upon request or termination of discussions between the parties, each party shall promptly return "
            "or destroy all documents and materials containing the other party's Confidential Information.",
        ),
    ],
}

CASES: dict[str, dict] = {
    "in_re_acme_indemnification.docx": {
        "jurisdiction": "Delaware",
        "sections": [
            (
                "1. Indemnification Cap Interpretation",
                "The court held that an indemnification cap tied to 'fees paid in the preceding twelve months' "
                "is measured as of the date the indemnified claim is asserted, not the date of contract signing, "
                "absent clear language to the contrary.",
            ),
            (
                "2. Gross Negligence Carve-Out",
                "The court narrowly construed the gross negligence carve-out, holding that ordinary negligence "
                "in performing contractual duties does not rise to gross negligence absent a showing of reckless "
                "indifference to the rights of others.",
            ),
            (
                "3. Enforceability of Liability Caps",
                "The court reaffirmed that limitation-of-liability clauses excluding consequential damages are "
                "enforceable between sophisticated commercial parties absent unconscionability or a statutory "
                "prohibition.",
            ),
        ],
    },
    "doe_v_software_vendor.docx": {
        "jurisdiction": "California",
        "sections": [
            (
                "1. Warranty Disclaimer Enforceability",
                "The court held that a conspicuous 'as is' warranty disclaimer in a commercial software license "
                "is enforceable against a sophisticated corporate licensee, even absent the word 'warranty' in "
                "capital letters, where the disclaimer was otherwise clear and unambiguous.",
            ),
            (
                "2. Non-Compete Reasonableness",
                "The court found a twelve-month, industry-specific non-compete provision unenforceable under "
                "California law, which generally prohibits non-compete restrictions on former employees except "
                "in narrow statutory circumstances.",
            ),
            (
                "3. Liquidated Damages Enforceability",
                "The court upheld a liquidated damages clause because the stipulated amount bore a reasonable "
                "relationship to the anticipated harm from breach and actual damages would have been difficult "
                "to ascertain at the time of contracting.",
            ),
        ],
    },
}


@dataclass
class GoldItem:
    id: str
    question: str
    scope: str  # "private" or "public"
    gold_filename: str
    gold_text_substring: str
    jurisdiction: str | None = None


def _gold_for_contracts() -> list[GoldItem]:
    questions = {
        "master_services_agreement.docx": [
            "Who must indemnify whom under the master services agreement, and what's excluded?",
            "Is there a cap on liability in the master services agreement, and does it cover consequential damages?",
            "What confidentiality obligations does each party have under the master services agreement?",
            "On what notice can either party terminate the master services agreement for breach?",
            "What law governs the master services agreement?",
        ],
        "employment_agreement.docx": [
            "How long does the non-competition restriction last after employment ends?",
            "What severance is owed if the employee is terminated without cause?",
            "Who owns inventions the employee creates during employment?",
            "Is the employment relationship at-will?",
            "How are disputes under the employment agreement resolved?",
        ],
        "commercial_lease.docx": [
            "How much does base rent increase each year under the commercial lease?",
            "Who is responsible for maintaining the roof and building systems?",
            "Can the tenant sublet the premises without consent?",
            "What happens if the tenant is late paying rent?",
            "What minimum general liability insurance must the tenant carry?",
        ],
        "software_license_agreement.docx": [
            "Is the software license exclusive, and what can the licensee use it for?",
            "Does the licensor provide any warranty on the software?",
            "How long does the licensor provide bug-fix support after delivery?",
            "How often can the licensor audit the licensee's software usage?",
            "Are there export control restrictions on the licensed software?",
        ],
        "merger_agreement.docx": [
            "What does the target represent about its financial statements in the merger agreement?",
            "What must happen before the parties are obligated to close the merger?",
            "How much of the purchase price is held in escrow for indemnification claims, and for how long?",
            "Under what circumstances can the acquirer terminate the merger agreement before closing?",
            "What termination fee applies if the target accepts a superior proposal?",
        ],
        "mutual_nda.docx": [
            "How does the mutual NDA define confidential information?",
            "What information is excluded from confidentiality under the NDA?",
            "How long do confidentiality obligations survive under the NDA?",
            "What remedy is available for unauthorized disclosure under the NDA?",
            "What must a party do with confidential materials when the discussions end?",
        ],
    }
    items = []
    for filename, qs in questions.items():
        sections = CONTRACTS[filename]
        for (heading, body), question in zip(sections, qs):
            items.append(
                GoldItem(
                    id=f"{filename}:{heading.split('.')[0]}",
                    question=question,
                    scope="private",
                    gold_filename=filename,
                    gold_text_substring=body[:60],
                )
            )
    return items


def _gold_for_cases() -> list[GoldItem]:
    questions = {
        "in_re_acme_indemnification.docx": [
            "As of what date is an indemnification cap tied to 'fees paid in the preceding twelve months' measured?",
            "How did the court construe the gross negligence carve-out in the indemnification clause?",
            "Are limitation-of-liability clauses excluding consequential damages enforceable between commercial parties?",
        ],
        "doe_v_software_vendor.docx": [
            "Is an 'as is' warranty disclaimer enforceable against a sophisticated corporate software licensee?",
            "Did the court enforce a twelve-month non-compete against a former employee under California law?",
            "What made the liquidated damages clause enforceable in the software vendor case?",
        ],
    }
    items = []
    for filename, qs in questions.items():
        case = CASES[filename]
        for (heading, body), question in zip(case["sections"], qs):
            items.append(
                GoldItem(
                    id=f"{filename}:{heading.split('.')[0]}",
                    question=question,
                    scope="public",
                    gold_filename=filename,
                    gold_text_substring=body[:60],
                    jurisdiction=case["jurisdiction"],
                )
            )
    return items


GOLD_QA: list[GoldItem] = _gold_for_contracts() + _gold_for_cases()
