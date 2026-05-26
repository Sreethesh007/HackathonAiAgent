#!/usr/bin/env python3
"""
Knowledge Base Seeder — seeds ChromaDB with medical guideline documents.
Compatible with chromadb >= 1.0 and sentence-transformers >= 3.0.

Embedding:  sentence-transformers/all-MiniLM-L6-v2 (local, free, 22 MB)
            No API keys required. Model downloads automatically on first run.

Usage:
    python scripts/seed_knowledge.py          # seed (skip existing)
    python scripts/seed_knowledge.py --reset  # wipe and reseed from scratch
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.observability.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

# ── Built-in clinical guidelines (18 documents) ──────────────────────────────
#
# Covers: emergency, urgent, and routine triage categories.
# Each document is a self-contained, dense clinical reference optimised for
# semantic similarity retrieval (key terms and synonyms are included inline).

BUILTIN_DOCUMENTS = [
    # ── EMERGENCY ────────────────────────────────────────────────────────────
    {
        "id": "who-triage-001",
        "title": "WHO Emergency Triage Assessment (ABCDE)",
        "category": "emergency",
        "content": (
            "Emergency triage ABCDE framework: Airway — ensure airway is open, reposition head-tilt "
            "chin-lift if unconscious. Breathing — look listen feel, administer O2 if SpO2 < 94%. "
            "Circulation — control severe bleeding with direct pressure, check pulse rate and quality. "
            "Disability — assess GCS, pupil response, blood glucose. Exposure — remove clothing to "
            "identify hidden injuries, prevent hypothermia. Immediate life threats requiring 112: "
            "cardiac arrest, respiratory failure, uncontrolled haemorrhage, anaphylaxis, stroke, "
            "major trauma, status epilepticus, eclampsia. Time-critical: every minute without "
            "treatment worsens outcome in cardiac and stroke emergencies."
        ),
    },
    {
        "id": "cardiac-acs-001",
        "title": "Acute Coronary Syndrome — Pre-hospital Protocol",
        "category": "emergency",
        "content": (
            "Acute Coronary Syndrome (ACS) including STEMI, NSTEMI, and unstable angina. "
            "Signs and symptoms: crushing, squeezing, or pressure chest pain, pain radiating to "
            "left arm, jaw, neck, or back, diaphoresis (sweating), nausea, vomiting, shortness of "
            "breath, palpitations, sense of impending doom. Atypical presentation in women and "
            "diabetics: fatigue, indigestion, back pain without chest pain. "
            "Pre-hospital actions: call 112 immediately, chew 300–325 mg aspirin (not swallow) "
            "unless allergic, rest in semi-recumbent position, unlock front door for paramedics, "
            "do not eat or drink, do not drive yourself. Time is muscle — every 10-minute delay "
            "in reperfusion causes irreversible myocardial damage. Target door-to-balloon < 90 min."
        ),
    },
    {
        "id": "stroke-fast-001",
        "title": "Stroke Recognition and FAST Protocol",
        "category": "emergency",
        "content": (
            "Stroke FAST-BE assessment: Face drooping or asymmetry, Arm weakness or drift, "
            "Speech slurred or confused, Time to call 112, Balance disturbance, Eye vision changes "
            "(sudden blurred or double vision, or loss of vision one eye). "
            "Additional warning signs: sudden severe headache ('worst headache of my life') "
            "suggesting subarachnoid haemorrhage, sudden dizziness, loss of coordination. "
            "Ischaemic stroke (87%): clot blocking cerebral artery — thrombolysis (tPA) within "
            "4.5 hours of onset, thrombectomy within 24 hours if eligible. "
            "Haemorrhagic stroke (13%): blood vessel rupture — lower BP, reverse anticoagulation. "
            "Action: call 112 now, note exact time of symptom onset, do not give aspirin until "
            "CT scan excludes haemorrhagic stroke. Brain tissue loss: 1.9 million neurons/minute "
            "without treatment. Do not let patient sleep off symptoms."
        ),
    },
    {
        "id": "anaphylaxis-001",
        "title": "Anaphylaxis — Recognition and Epinephrine Protocol",
        "category": "emergency",
        "content": (
            "Anaphylaxis is a severe, life-threatening systemic hypersensitivity reaction. "
            "Triggers: foods (peanuts, tree nuts, shellfish, milk, eggs), medications (penicillin, "
            "NSAIDs, contrast media), insect stings, latex, exercise-induced. "
            "Signs: hives, urticaria, angioedema (lip/tongue/throat swelling), stridor, wheeze, "
            "bronchospasm, hypotension, tachycardia, dizziness, loss of consciousness, vomiting. "
            "Biphasic reaction: symptoms may recur 1–72 hours after initial episode. "
            "Treatment: epinephrine (adrenaline) 0.3–0.5 mg IM (outer mid-thigh) immediately — "
            "this is first-line, not antihistamines. Call 112. Lay patient flat with legs elevated "
            "(unless respiratory distress — then sit up). Repeat epinephrine after 5 minutes if "
            "no improvement. Observe minimum 4–6 hours post-reaction even if resolved."
        ),
    },
    {
        "id": "respiratory-distress-001",
        "title": "Respiratory Distress — Asthma and Acute Breathlessness",
        "category": "emergency",
        "content": (
            "Acute severe asthma (life-threatening): SpO2 < 92%, PEF < 33% predicted, silent chest "
            "on auscultation, cyanosis, exhaustion, confusion, bradycardia. "
            "Moderate asthma: SpO2 >= 92%, PEF 33–50%, able to complete sentences. "
            "Differential diagnosis for acute breathlessness: asthma, COPD exacerbation, "
            "pulmonary embolism (PE), pneumothorax, pneumonia, cardiac failure, foreign body. "
            "Red flags requiring 112: respiratory rate > 30/min, SpO2 < 90% on air, accessory "
            "muscle use, inability to speak in full sentences, altered consciousness. "
            "Pre-hospital: sit patient upright, give salbutamol 2.5–5 mg nebulised or 4–10 puffs "
            "via spacer every 20 min, supplemental O2 to target SpO2 94–98%, call 112 immediately "
            "for severe or life-threatening features."
        ),
    },
    {
        "id": "sepsis-001",
        "title": "Sepsis — Early Warning Signs and Sepsis-3 Criteria",
        "category": "emergency",
        "content": (
            "Sepsis: life-threatening organ dysfunction caused by dysregulated host response to "
            "infection. Septic shock: sepsis with vasopressor requirement to maintain MAP >= 65 mmHg "
            "and serum lactate > 2 mmol/L despite adequate fluid resuscitation — mortality 30–40%. "
            "qSOFA red flags (score >= 2 = high risk): respiratory rate >= 22/min, altered mental "
            "status (new confusion, agitation), systolic BP <= 100 mmHg. "
            "Common sources: pneumonia, urinary tract infection, abdominal infection, skin and soft "
            "tissue, meningitis, IV line infection. "
            "Symptoms: fever > 38.3°C or hypothermia < 36°C, rigors (shaking chills), rapid heart "
            "rate, rapid breathing, confusion, extreme fatigue, mottled skin. "
            "The Sepsis Six (first hour): high-flow O2, blood cultures x2, IV antibiotics, IV fluids "
            "500 mL bolus, measure lactate, monitor urine output. call 112 immediately."
        ),
    },

    # ── URGENT ───────────────────────────────────────────────────────────────
    {
        "id": "headache-001",
        "title": "Headache Assessment — Red Flags and Triage Protocol",
        "category": "urgent",
        "content": (
            "Headache red flags requiring immediate emergency evaluation (call 112 or go to ER): "
            "thunderclap headache — sudden onset, worst headache of life (subarachnoid haemorrhage "
            "until proven otherwise), fever + stiff neck + photophobia (bacterial meningitis), "
            "new headache after age 50 (giant cell arteritis, space-occupying lesion), "
            "headache with focal neurological symptoms (weakness, vision loss, speech disturbance), "
            "headache following head trauma, headache waking from sleep, progressive worsening, "
            "headache in immunocompromised or cancer patients. "
            "Urgent (GP within 24 hours): headache persisting > 72 hours unresponsive to OTC, "
            "new pattern significantly different from usual headaches. "
            "Routine (known migraine or tension): ibuprofen 400 mg with food, paracetamol 1 g, "
            "dark quiet room, cool compress, adequate hydration. Triptan if prescribed."
        ),
    },
    {
        "id": "fever-001",
        "title": "Fever Assessment — Triage and Management Guidelines",
        "category": "urgent",
        "content": (
            "Fever definitions: low-grade 37.3–38°C, moderate 38–39°C, high 39–40°C, "
            "hyperpyrexia > 40°C (medical emergency). "
            "Emergency (call 112): temperature > 40°C, infant < 3 months any fever, "
            "fever + stiff neck + non-blanching rash (meningococcal septicaemia — glass test), "
            "fever + confusion or altered consciousness, fever + difficulty breathing, "
            "fever + severe headache + photophobia. "
            "Urgent (GP within 24 hours): fever persisting > 3 days, fever with localising signs "
            "(ear pain, throat exudate, dysuria), immunocompromised patient any fever. "
            "Fever management: paracetamol 500–1000 mg every 4–6 h (max 4 g/day), ibuprofen "
            "400 mg with food every 6–8 h, tepid sponging, increase oral fluids 2–3 L/day, rest."
        ),
    },
    {
        "id": "paediatric-fever-001",
        "title": "Paediatric Fever — NICE Traffic Light System",
        "category": "urgent",
        "content": (
            "Paediatric fever NICE traffic light — GREEN (low risk): normal colour, "
            "responds normally to social cues, content/smiling, stays awake or awakens quickly, "
            "strong normal cry, normal skin and eyes, moist mucous membranes, no red or amber features. "
            "AMBER (intermediate risk): pallor of face/lips, not responding normally, no smile, "
            "wakes only with prolonged stimulation, decreased activity, nasal flaring, "
            "capillary refill >= 3 seconds, dry mucous membranes, reduced urine output, fever > 5 days. "
            "RED (high risk — refer to ED immediately): pale/mottled/ashen/blue, no response to "
            "social cues, appears ill to clinician, does not wake or if roused will not stay awake, "
            "weak high-pitched or continuous cry, grunting, moderate-severe chest indrawing, "
            "non-blanching rash, bulging fontanelle, neck stiffness, status epilepticus, "
            "temperature > 38°C in child < 3 months, > 39°C age 3–6 months."
        ),
    },
    {
        "id": "abdominal-pain-001",
        "title": "Abdominal Pain — Red Flags and Differential Assessment",
        "category": "urgent",
        "content": (
            "Abdominal pain red flags requiring emergency assessment: severe sudden-onset pain "
            "(aortic aneurysm rupture, mesenteric ischaemia, perforated viscus), "
            "rigid board-like abdomen (peritonitis), pain with haemodynamic instability "
            "(shock, syncope, tachycardia), vomiting blood or passing fresh blood PR, "
            "pregnancy with abdominal pain (ectopic pregnancy until excluded), "
            "pain after recent abdominal surgery (anastomotic leak, obstruction). "
            "Urgent causes: appendicitis (right iliac fossa, rebound tenderness, Rovsing's sign), "
            "acute cholecystitis (right upper quadrant, Murphy's sign, post-fatty meal), "
            "urinary tract obstruction/renal colic (loin to groin radiation, haematuria). "
            "Assessment: site, onset, character, radiation, associations (nausea, vomiting, "
            "fever, change in bowel habit, urinary symptoms), timing, exacerbating/relieving factors, severity."
        ),
    },
    {
        "id": "mental-health-crisis-001",
        "title": "Mental Health Crisis — Suicidal Ideation and Acute Psychiatric Emergency",
        "category": "urgent",
        "content": (
            "Mental health crisis assessment — risk of suicide and self-harm. "
            "Ask directly: 'Are you having thoughts of ending your life?' — asking does not increase risk. "
            "High-risk features: specific plan and means available, previous attempt (strongest predictor), "
            "recent significant loss, social isolation, substance misuse, male gender over 45, "
            "access to lethal means (firearms, medications), stating goodbye, giving possessions away. "
            "Immediate action (high risk): call 112 or take to emergency department, do not leave "
            "person alone, remove access to means if safe to do so, involve trusted person. "
            "Urgent (lower risk with protective factors): same-day mental health crisis line, "
            "emergency GP appointment, crisis team referral. "
            "Crisis lines: Samaritans 116 123, Crisis Text Line text HELLO to 85258. "
            "Protective factors: social support, reasons for living, future planning, help-seeking behaviour."
        ),
    },
    {
        "id": "diabetes-hypoglycaemia-001",
        "title": "Diabetes — Hypoglycaemia Recognition and Management",
        "category": "urgent",
        "content": (
            "Hypoglycaemia: blood glucose < 4.0 mmol/L (72 mg/dL). "
            "Symptoms: shaking/trembling, sweating, palpitations, pallor, anxiety (adrenergic) — "
            "confusion, difficulty concentrating, slurred speech, visual disturbance, seizures, "
            "loss of consciousness (neuroglycopenic — more severe). "
            "Hypoglycaemia unawareness: common after longstanding diabetes, requires lower BG targets. "
            "Mild-moderate (conscious and able to swallow): 15–20 g fast-acting carbohydrate — "
            "150–200 mL fruit juice, 5–7 glucose tablets, 4–5 jelly babies. Recheck glucose 15 min. "
            "Repeat if still < 4 mmol/L. Follow with long-acting carbohydrate snack. "
            "Severe (impaired consciousness, unable to swallow): call 112, IM glucagon 1 mg "
            "(if available and trained), place recovery position, IV 10% glucose if in hospital. "
            "Hyperglycaemic emergencies: DKA (type 1, ketones > 3, pH < 7.3) and HHS "
            "(type 2, glucose > 30, osmolality > 320) both require hospital admission and IV fluids."
        ),
    },

    # ── ROUTINE ──────────────────────────────────────────────────────────────
    {
        "id": "hypertension-001",
        "title": "Hypertension — Classification and Management Guidelines",
        "category": "routine",
        "content": (
            "Blood pressure classification (ESC/ESH 2023): Optimal < 120/80, Normal 120–129/80–84, "
            "High-normal 130–139/85–89, Grade 1 HTN 140–159/90–99, Grade 2 HTN 160–179/100–109, "
            "Grade 3 HTN >= 180/110, Hypertensive urgency >= 180/120 without organ damage, "
            "Hypertensive emergency >= 180/120 with acute organ damage (encephalopathy, AKI, "
            "aortic dissection, pulmonary oedema) — requires immediate IV treatment. "
            "Lifestyle modifications: DASH diet, sodium < 2 g/day, alcohol < 14 units/week, "
            "150 min moderate aerobic exercise/week, weight loss (target BMI < 25), quit smoking. "
            "Pharmacotherapy first-line: ACE inhibitor or ARB, calcium channel blocker, thiazide "
            "diuretic (depending on age, ethnicity, comorbidities). "
            "Monitoring: home BP monitoring twice daily for 7 days, clinic review every 1–3 months "
            "until controlled, then every 6 months when stable."
        ),
    },
    {
        "id": "uti-001",
        "title": "Urinary Tract Infection — Assessment and Management",
        "category": "routine",
        "content": (
            "Urinary tract infection (UTI) classification: uncomplicated (lower UTI/cystitis in "
            "non-pregnant women without structural abnormality), complicated (men, pregnancy, "
            "catheterised, immunocompromised, structural abnormality, pyelonephritis). "
            "Cystitis symptoms: dysuria (pain on urination), frequency, urgency, suprapubic pain, "
            "haematuria (blood in urine), offensive smelling urine, cloudy urine. "
            "Pyelonephritis (upper UTI): systemic features — fever, rigors, flank/loin pain, "
            "nausea, vomiting — requires urgent assessment and typically IV antibiotics if severe. "
            "Red flags: fever > 38°C with UTI symptoms (pyelonephritis), pregnancy + any UTI "
            "(treat immediately to prevent preterm labour), men with UTI (structural cause likely), "
            "recurrent UTI > 2/year, haematuria without dysuria (may be malignancy). "
            "Uncomplicated: trimethoprim 200 mg BD 7 days or nitrofurantoin 50 mg QDS 7 days. "
            "Increase fluid intake 2–3 L/day, urine alkalinising sachets for symptom relief."
        ),
    },
    {
        "id": "musculoskeletal-001",
        "title": "Musculoskeletal Pain — Back Pain and Soft Tissue Injuries",
        "category": "routine",
        "content": (
            "Non-specific low back pain (85–90% of cases): no identifiable structural cause, "
            "self-limiting — 90% resolve within 6 weeks with appropriate management. "
            "Red flags requiring urgent investigation: age of onset < 20 or > 55 years, "
            "violent trauma mechanism, thoracic pain, bilateral leg pain or numbness, "
            "bladder or bowel dysfunction (cauda equina syndrome — surgical emergency), "
            "saddle anaesthesia, progressive neurological deficit, systemically unwell, "
            "history of malignancy, steroid use, HIV, weight loss. "
            "Management of non-specific LBP: stay active (bed rest worsens outcome), "
            "paracetamol 1 g QDS + ibuprofen 400 mg TDS (short course with food), "
            "hot/cold packs, physiotherapy for persistent symptoms > 6 weeks, "
            "consider spinal manipulation, consider referral for psychological support if chronic. "
            "Soft tissue injuries PRICE: Protection, Rest, Ice (20 min every 2 h for 48 h), "
            "Compression bandage, Elevation. Return to activity as tolerated."
        ),
    },
    {
        "id": "medication-adherence-001",
        "title": "Medication Adherence and Chronic Disease Management",
        "category": "routine",
        "content": (
            "Medication non-adherence affects 30–50% of patients with chronic diseases and is a "
            "leading cause of preventable hospitalisations and disease progression. "
            "Common barriers: side effects, complex regimens, cost, forgetfulness, health beliefs, "
            "difficulty swallowing tablets, cognitive impairment. "
            "Strategies to improve adherence: simplify regimen (once daily preferred), "
            "medication reminder apps or pill organisers, blister packaging, "
            "auto-repeat prescriptions, patient education on why each medication matters, "
            "review at every appointment, address side effects rather than stopping. "
            "Never stop the following abruptly without medical guidance: beta-blockers (rebound "
            "tachycardia, angina), corticosteroids (adrenal insufficiency), SSRIs (discontinuation "
            "syndrome), antiepileptics (seizures), antihypertensives (rebound hypertension). "
            "Prescription refill — routine visit: schedule GP appointment 2 weeks before running out."
        ),
    },
    {
        "id": "preventive-care-001",
        "title": "Preventive Care and General Wellness Guidelines",
        "category": "routine",
        "content": (
            "NHS/WHO preventive care recommendations: Physical activity — 150 min moderate-intensity "
            "or 75 min vigorous aerobic activity per week, plus muscle-strengthening 2 days/week. "
            "Diet: 5 portions fruit and vegetables daily, limit red/processed meat, "
            "< 6 g salt/day, < 30 g saturated fat/day, limit ultra-processed foods. "
            "Alcohol: < 14 units/week men and women, spread over 3+ days, alcohol-free days. "
            "Smoking: cessation reduces cardiovascular risk to near-normal within 1 year; "
            "refer to NHS Stop Smoking Service, offer NRT and varenicline/bupropion. "
            "Screening programmes: breast cancer (age 50–70, every 3 years), cervical (25–64, "
            "3–5 years), bowel (60–74, every 2 years FIT), abdominal aortic aneurysm (men at 65). "
            "Vaccinations: annual influenza (over 65, chronic disease, pregnant), "
            "COVID-19 boosters, pneumococcal (over 65), shingles (70–79). "
            "Mental wellbeing: sleep 7–9 h/night, social connection, mindfulness, NHS Talking Therapies."
        ),
    },

    # ── GENERAL ──────────────────────────────────────────────────────────────
    {
        "id": "general-triage-001",
        "title": "General Triage Decision Framework",
        "category": "general",
        "content": (
            "Triage severity scale 0–10: "
            "EMERGENCY (8–10) — cardiac arrest, stroke, anaphylaxis, major haemorrhage, respiratory "
            "failure, major trauma, status epilepticus, septic shock, eclampsia — call 112 immediately. "
            "URGENT (5–7) — high fever, severe uncontrolled pain, suspected fracture, suspected "
            "appendicitis, acute mental health crisis, DKA, pyelonephritis, worsening chronic disease — "
            "seek care within 2–4 hours at urgent care or A&E. "
            "ROUTINE (1–4) — stable chronic disease management, prescription refills, minor illness, "
            "mild infections, non-urgent musculoskeletal pain, routine screening — "
            "schedule GP appointment within 1 week. "
            "SELF-CARE (0–1) — common cold, minor cuts, mild sore throat, mild tension headache — "
            "manage at home with OTC medications and rest. "
            "Safety net: any patient who is deteriorating or developing new symptoms should be "
            "reassessed and escalated to a higher triage level without delay."
        ),
    },
]


# ── Embedding function factory ────────────────────────────────────────────────

def _make_embedding_fn():
    """
    Build a ChromaDB-compatible embedding function using sentence-transformers.

    Model: all-MiniLM-L6-v2
      - 22 MB download (cached to ~/.cache/huggingface/)
      - 384-dimensional embeddings
      - Runs fully offline after first download
      - Excellent semantic similarity for short medical texts

    Falls back to a hash-based stub if sentence-transformers is not installed
    so that the seeder can at least store documents (search quality will be poor).
    """
    model_name = settings.embedding_model  # "all-MiniLM-L6-v2" by default

    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        print(f"  ✓ Using sentence-transformers embedding: {model_name}")
        return SentenceTransformerEmbeddingFunction(model_name=model_name)
    except ImportError:
        print(
            "  ⚠ sentence-transformers not installed — falling back to hash embeddings.\n"
            "    Run: pip install sentence-transformers"
        )
        return _hash_embedding_fallback()


def _hash_embedding_fallback():
    """Deterministic hash-based stub — used only if sentence-transformers is missing."""
    import hashlib
    from chromadb.api.types import Documents, Embeddings, EmbeddingFunction

    class _HashEmbedFn(EmbeddingFunction):
        def name(self) -> str:
            return "hash-fallback-v1"

        def __call__(self, input: Documents) -> Embeddings:
            dim = 384
            out = []
            for text in input:
                seed = hashlib.sha256(str(text).encode()).digest()
                raw = list(seed) * (dim // 32 + 1)
                vec = [(b / 127.5 - 1.0) for b in raw[:dim]]
                norm = sum(v ** 2 for v in vec) ** 0.5 or 1.0
                out.append([v / norm for v in vec])
            return out

        def build_from_config(self, config):
            return _HashEmbedFn()

        def get_config(self):
            return {}

    return _HashEmbedFn()


# ── PDF chunking ─────────────────────────────────────────────────────────────

def _clean_pdf_text(text: str) -> str:
    """Remove common PDF extraction artifacts."""
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove page numbers (isolated digits on a line)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    # Remove headers/footers that repeat on every page (simple heuristic)
    text = re.sub(r"[ \t]{3,}", " ", text)
    return text.strip()


def _sentence_aware_chunks(text: str, max_chars: int = 800, overlap_chars: int = 150) -> list[str]:
    """
    Split text into overlapping chunks that respect sentence boundaries.

    Strategy:
      1. Split into sentences on ". " boundaries.
      2. Accumulate sentences until chunk exceeds max_chars.
      3. Start next chunk with the last sentence of the previous chunk (overlap).
    """
    # Split on sentence boundaries
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)
        if current_len + sentence_len > max_chars and current:
            chunk_text = " ".join(current)
            chunks.append(chunk_text)
            # Overlap: keep last sentence(s) from current chunk
            overlap: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) <= overlap_chars:
                    overlap.insert(0, s)
                    overlap_len += len(s)
                else:
                    break
            current = overlap + [sentence]
            current_len = sum(len(s) for s in current)
        else:
            current.append(sentence)
            current_len += sentence_len

    if current:
        chunks.append(" ".join(current))

    return chunks


# ── Main seeder ──────────────────────────────────────────────────────────────

def seed_knowledge_base(reset: bool = False) -> None:
    try:
        import chromadb
    except ImportError:
        print("Error: chromadb is not installed. Run: pip install chromadb")
        sys.exit(1)

    settings.ensure_dirs()
    persist_dir = str(settings.chroma_persist_dir)
    collection_name = settings.chroma_collection_name

    print(f"\n{'═' * 55}")
    print(f"  Healthcare Triage — Knowledge Base Seeder")
    print(f"{'═' * 55}")
    print(f"  ChromaDB location : {persist_dir}")
    print(f"  Collection        : {collection_name}")
    print(f"  Embedding model   : {settings.embedding_model}")
    print(f"{'─' * 55}\n")

    client = chromadb.PersistentClient(path=persist_dir)

    if reset:
        try:
            client.delete_collection(collection_name)
            print(f"  ✓ Deleted existing collection: {collection_name}\n")
        except Exception:
            pass

    ef = _make_embedding_fn()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=ef,
    )

    existing_count = collection.count()
    print(f"  Existing documents : {existing_count}")
    print(f"\n  Seeding {len(BUILTIN_DOCUMENTS)} built-in guidelines...\n")

    # Upsert built-in documents
    ids, docs, metas = [], [], []
    for d in BUILTIN_DOCUMENTS:
        ids.append(d["id"])
        docs.append(d["content"])
        metas.append({
            "title": d["title"],
            "category": d["category"],
            "source": "built-in",
            "chunk_index": 0,
            "total_chunks": 1,
        })
        print(f"  + [{d['category']:10s}] {d['title']}")

    collection.upsert(ids=ids, documents=docs, metadatas=metas)

    # Load and chunk PDFs from data/knowledge/ if present
    knowledge_dir = Path("data/knowledge")
    pdf_count = 0
    if knowledge_dir.exists():
        pdf_files = list(knowledge_dir.glob("*.pdf"))
        if pdf_files:
            print(f"\n  Processing {len(pdf_files)} PDF(s) from {knowledge_dir}...\n")
        for pdf_path in pdf_files:
            try:
                from pypdf import PdfReader
                raw_text = "\n".join(
                    p.extract_text() or "" for p in PdfReader(str(pdf_path)).pages
                )
                clean_text = _clean_pdf_text(raw_text)
                chunks = _sentence_aware_chunks(clean_text, max_chars=800, overlap_chars=150)

                pdf_ids, pdf_docs, pdf_metas = [], [], []
                for i, chunk in enumerate(chunks):
                    if not chunk.strip():
                        continue
                    pdf_ids.append(f"pdf-{pdf_path.stem}-{i:04d}")
                    pdf_docs.append(chunk)
                    pdf_metas.append({
                        "title": pdf_path.stem.replace("_", " ").replace("-", " ").title(),
                        "category": "pdf",
                        "source": str(pdf_path),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    })

                if pdf_ids:
                    collection.upsert(ids=pdf_ids, documents=pdf_docs, metadatas=pdf_metas)
                    pdf_count += len(pdf_ids)
                    print(f"  + [pdf       ] {pdf_path.name}  ({len(pdf_ids)} chunks)")
            except Exception as e:
                print(f"  ! {pdf_path.name}: {e}")

    final_count = collection.count()
    new_docs = final_count - existing_count

    print(f"\n{'═' * 55}")
    print(f"  ✓ Collection     : {collection_name}")
    print(f"  ✓ Total docs     : {final_count}  (+{new_docs} new)")
    if pdf_count:
        print(f"  ✓ PDF chunks     : {pdf_count}")
    print(f"  ✓ Location       : {persist_dir}")
    print(f"{'═' * 55}")

    # Verification queries
    print("\n  Verification — semantic similarity test queries:\n")
    test_queries = [
        ("chest pain radiating to arm", "cardiac-acs-001"),
        ("sudden worst headache ever", "stroke-fast-001"),
        ("child has fever and stiff neck", "paediatric-fever-001"),
        ("feeling shaky sweating low blood sugar", "diabetes-hypoglycaemia-001"),
    ]

    for query, expected_id in test_queries:
        try:
            results = collection.query(query_texts=[query], n_results=2)
            top_meta = results["metadatas"][0][0] if results["metadatas"] else {}
            top_id = results["ids"][0][0] if results["ids"] else "?"
            top_dist = results["distances"][0][0] if results["distances"] else 1.0
            similarity = round(1.0 - top_dist, 3)
            hit = "✓" if top_id == expected_id else "~"
            print(f"  {hit} Query : '{query}'")
            print(f"    → [{top_meta.get('category', '?')}] {top_meta.get('title', '?')}")
            print(f"       similarity={similarity:.3f}  (expected: {expected_id})\n")
        except Exception as e:
            print(f"  ! Query '{query}' failed: {e}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the medical knowledge base")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate collection before seeding")
    args = parser.parse_args()
    seed_knowledge_base(reset=args.reset)
