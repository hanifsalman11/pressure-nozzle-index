import os
import json
import re
import time
import math
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://hanifsalman11.github.io/pressure-nozzle-index").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4").strip()
CUSTOM_WASHER = os.environ.get("CUSTOM_WASHER", "").strip()
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "3"))

DOCS_DIR = "docs"
DATA_DIR = "data"
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_washers.json")
MONETIZATION_FILE = os.path.join(DATA_DIR, "monetization.json")

# Format: (Model / Setup Name, Max PSI, Flow GPM, Pump & Engine Type, Hose Inner Dia)
SEED_WASHERS = [
    ("Simpson PowerShot PS4240 4200 PSI 4.0 GPM Honda GX390", 4200, 4.0, "Honda GX390 + AAA Triplex", "3/8-Inch QC"),
    ("Simpson MegaShot MS60763-S 3300 PSI 2.4 GPM Honda GC190", 3300, 2.4, "Honda GC190 + Axial Cam", "1/4-Inch M22"),
    ("Simpson Aluminum ALH4240 4200 PSI 4.0 GPM CAT Triplex", 4200, 4.0, "Honda GX390 + CAT Triplex", "3/8-Inch QC"),
    ("DeWalt DXPW3835 3800 PSI 3.5 GPM Honda GX270 Commercial", 3800, 3.5, "Honda GX270 + AAA Triplex", "3/8-Inch QC"),
    ("DeWalt DXPW4240 4200 PSI 4.0 GPM Honda GX390 Pro", 4200, 4.0, "Honda GX390 + Triplex Pump", "3/8-Inch QC"),
    ("DeWalt DXPW3425 3400 PSI 2.5 GPM Honda GX200", 3400, 2.5, "Honda GX200 + Triplex Pump", "5/16-Inch M22"),
    ("Westinghouse WPX3400 3400 PSI 2.6 GPM Gas Washer", 3400, 2.6, "Westinghouse 212cc Axial", "1/4-Inch M22"),
    ("Westinghouse WPX4400 4400 PSI 4.2 GPM Commercial", 4400, 4.2, "420cc OHV + Brass Triplex", "3/8-Inch QC"),
    ("Generac SpeedWash 3200 PSI 2.7 GPM PowerDial Washer", 3200, 2.7, "Generac 196cc OHV Axial", "1/4-Inch M22"),
    ("Generac Pro 4200 PSI 4.0 GPM Belt-Drive Triplex", 4200, 4.0, "Generac 420cc + Belt Triplex", "3/8-Inch QC"),
    ("Predator 4400 PSI 4.2 GPM Commercial Duty Gas Washer", 4400, 4.2, "Predator 420cc + AR Triplex", "3/8-Inch QC"),
    ("Predator 3200 PSI 2.8 GPM 212cc Gas Pressure Washer", 3200, 2.8, "Predator 212cc Axial Pump", "1/4-Inch M22"),
    ("Champion 4200 PSI 4.0 GPM Commercial AR Triplex", 4200, 4.0, "Champion 389cc + AR Triplex", "3/8-Inch QC"),
    ("Ryobi RY803325 3300 PSI 2.5 GPM Honda GCV170 Washer", 3300, 2.5, "Honda GCV170 Axial Cam", "1/4-Inch M22"),
    ("Craftsman CMXGWAS021049 3400 PSI 2.5 GPM Briggs", 3400, 2.5, "Briggs CR950 Axial Pump", "1/4-Inch M22"),
    ("Active 2.0 Electric Car Detailing Washer (1800 PSI 2.0 GPM)", 1100, 2.0, "5-Piston Brushless Induction", "3/8-Inch Swivel"),
    ("AR Blue Clean AR630-TSS Pro 1900 PSI 2.1 GPM Electric", 1900, 2.1, "Annovi Reverberi Triplex", "3/8-Inch Swivel"),
    ("Kranzle K1122TST 1400 PSI 2.1 GPM Pro Detailing Rig", 1400, 2.1, "Kranzle Forged Brass Plunger", "3/8-Inch Braided"),
    ("BE Power Equipment B4213HTBS 4200 PSI 4.0 GPM CAT Pump", 4200, 4.0, "Honda GX390 + CAT 67DX", "3/8-Inch QC"),
    ("Mi-T-M CW-3004 3000 PSI 3.5 GPM Belt-Drive Industrial", 3000, 3.5, "Honda GX390 Belt-Drive", "3/8-Inch QC"),
    ("NorthStar 4000 PSI 3.5 GPM Honda GX270 CAT Triplex", 4000, 3.5, "Honda GX270 + CAT 4DNX", "3/8-Inch QC"),
    ("5.5 GPM 3500 PSI Skid-Mount Commercial Trailer Rig", 3500, 5.5, "Honda GX630 + Udor Belt Pump", "3/8-Inch 2-Wire"),
    ("8.0 GPM 3500 PSI V-Twin Commercial Flatwork Rig", 3500, 8.0, "Honda GX690 + General TS2021", "1/2-Inch 2-Wire"),
    ("4.0 GPM 4000 PSI Driveway Surface Cleaner Sizing", 4000, 4.0, "Commercial Direct/Belt Triplex", "3/8-Inch QC"),
    ("2.5 GPM 3000 PSI Residential Surface Cleaner Sizing", 3000, 2.5, "Residential Axial/Triplex", "1/4-Inch or 3/8\""),
    ("3.0 GPM 3200 PSI Mid-Range Pressure Washer Sizing", 3200, 3.0, "Mid-Range Triplex Plunger", "3/8-Inch QC"),
    ("CAT Pumps 67DX39G1I & 4DNX27GSI Triplex Replacement", 4000, 3.9, "Direct-Drive Hollow Shaft", "3/8-Inch QC"),
    ("General Pump EZ4040G34 4000 PSI 4.0 GPM Triplex", 4000, 4.0, "1-Inch Hollow Shaft Triplex", "3/8-Inch QC"),
    ("Whisper Wash Classic 19-Inch Dual-Nozzle Bar Sizing", 4000, 4.5, "Twin-Tip Rotary Swivel Bar", "3/8-Inch QC"),
    ("BE Whirl-A-Way 16-Inch & 20-Inch Surface Cleaner Sizing", 4000, 4.0, "Dual-Nozzle 25025 Rotary Bar", "3/8-Inch QC")
]


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not parse {filepath}: {e}")
    return default


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def safe_float(val, default=4000.0):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(val))
        return float(cleaned) if cleaned else float(default)
    except Exception:
        return float(default)


def build_amazon_url(search_keywords, mon_cfg):
    domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")
    encoded_q = urllib.parse.quote_plus(search_keywords)
    return f"https://{domain}/s?k={encoded_q}&tag={tag}"


def discover_google_washer_queries():
    discovered = []
    seeds = [
        "what size surface cleaner for ",
        "simpson powershot ",
        "pressure washer nozzle size for ",
        "dewalt pressure washer "
    ]
    for seed in seeds:
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q={urllib.parse.quote(seed)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for suggestion in data[1]:
                    cleaned = suggestion.lower()
                    for pref in seeds:
                        if "what size" in pref or "nozzle size" in pref:
                            cleaned = cleaned.replace(pref, "")
                    cleaned = re.sub(
                        r"\b(calculator|size|sizing|chart|manual|review|reddit|for)\b",
                        "",
                        cleaned
                    ).strip()
                    if 5 <= len(cleaned) <= 42:
                        psi_m = re.search(r"(\d{4})\s*psi", cleaned)
                        psi_v = int(psi_m.group(1)) if psi_m else 4000
                        gpm_m = re.search(r"(\d(?:\.\d)?)\s*gpm", cleaned)
                        gpm_v = float(gpm_m.group(1)) if gpm_m else (4.0 if psi_v >= 3800 else 2.5)
                        discovered.append((cleaned.title(), psi_v, gpm_v, "Commercial Triplex Plunger", "3/8-Inch QC"))
        except Exception as e:
            print(f"[WARN] Google Suggest notice: {e}")
    return discovered


def build_deterministic_washer_data(washer_tuple):
    """Mesin Fisika Hidrodinamika Orifice Bernoulli & Surface Cleaner (100% bebas gagal)."""
    model_name, psi, gpm, pump_type, hose_spec = washer_tuple

    # Rumus Standar Industri Ukuran Orifice Nosel: Orifice # = GPM * sqrt(4000 / PSI)
    raw_orifice = gpm * math.sqrt(4000.0 / max(500.0, float(psi)))
    orifice_size = round(raw_orifice * 2.0) / 2.0
    # Untuk Dual-Tip Surface Cleaner, ukuran orifice dibagi 2 per ujung semprotan (misal 25020 / 25025)
    sc_tip_orifice = round((raw_orifice / 2.0) * 4.0) / 4.0
    sc_tip_code = f"250{int(round(sc_tip_orifice * 10)):02d}"

    # Aturan 4-Inch per 1 GPM untuk Diameter Rotary Surface Cleaner:
    ideal_sc_inches = int(round(gpm * 4.0))
    cleaning_units = int(round(psi * gpm))
    # Gaya dorong balik (Recoil Force lbs) pada tombak semprot: F = 0.0526 * GPM * sqrt(PSI)
    recoil_lbs = round(0.0526 * gpm * math.sqrt(psi), 1)

    return {
        "washer_name": model_name,
        "pump_type": pump_type,
        "seo_title": f"{model_name} Orifice Nozzle, Surface Cleaner & PSI Calculator (2026)",
        "meta_description": f"Calculate exact nozzle orifice size (#{orifice_size:.1f}), max rotary surface cleaner diameter ({ideal_sc_inches}\"), dual-tip code ({sc_tip_code}), and {cleaning_units:,} Cleaning Units for {model_name}.",
        "specs": {
            "max_psi": psi,
            "flow_gpm": gpm,
            "cleaning_units": cleaning_units,
            "orifice_number": orifice_size,
            "surface_cleaner_inches": ideal_sc_inches,
            "surface_cleaner_tip_code": sc_tip_code,
            "wand_recoil_lbs": recoil_lbs,
            "pump_engine_spec": pump_type,
            "hose_spec": hose_spec
        },
        "fluid_verdict": f"Operating at {psi:,} PSI and {gpm} GPM ({cleaning_units:,} Cleaning Units), the {model_name} ({pump_type}) requires a #{orifice_size:.1f} orifice spray nozzle to achieve full rated pressure without unloader valve cycling. Following the commercial flatwork rule of 4 inches of deck width per 1.0 GPM of flow, pair this machine with a {ideal_sc_inches}-inch Stainless Rotary Surface Cleaner fitted with two #{sc_tip_orifice:.2f} ({sc_tip_code} MEG) 1/4\" NPT spray tips.",
        "hardware_bundle": [
            {
                "badge": f"{psi:,} PSI / {gpm} GPM Unit",
                "title": f"{model_name} High-Output Pressure Washer",
                "price_range": "$389 - $1,399",
                "amazon_query": f"{model_name} Pressure Washer",
                "wash_note": f"Delivers {cleaning_units:,} Cleaning Units with {recoil_lbs} lbs of wand recoil thrust."
            },
            {
                "badge": f"{ideal_sc_inches}\" Rotary Surface Cleaner",
                "title": f"{ideal_sc_inches}-Inch Heavy-Duty Stainless Steel Rotary Surface Cleaner (Dual {sc_tip_code} Tips)",
                "price_range": "$99 - $389",
                "amazon_query": f"{ideal_sc_inches} Inch Stainless Steel Pressure Washer Surface Cleaner 4000 PSI",
                "wash_note": f"Sized strictly at 4 inches per GPM ({gpm} GPM × 4 = {ideal_sc_inches}\") so the spray bar spins at 1,800+ RPM without tiger-striping concrete."
            },
            {
                "badge": f"#{orifice_size:.1f} Orifice & Injector Kit",
                "title": f"#{orifice_size:.1f} Orifice 5-Piece Quick-Connect Nozzle Tip Set + High-Draw Downstream Chemical Injector",
                "price_range": "$29 - $79",
                "amazon_query": f"Pressure Washer Nozzle Tips {orifice_size:.1f} Orifice Downstream Injector 3/8 QC",
                "wash_note": f"Matched #{orifice_size:.1f} orifice prevents unloader valve overheating, while a J-Rod 4-way soft-wash nozzle reaches 2nd-story siding."
            },
            {
                "badge": "100ft 3/8\" Braided Hose",
                "title": "100ft × 3/8-Inch Non-Marking Steel-Braided Pressure Washer Hose (4,500 PSI) + Swivel Gun",
                "price_range": "$109 - $229",
                "amazon_query": "100ft 3/8 Inch Non Marking Steel Braided Pressure Washer Hose 4500 PSI",
                "wash_note": "Upgrading from 1/4\" to 3/8\" inner-diameter braided hose cuts friction pressure loss by 65% over 100-foot driveway runs."
            }
        ],
        "operator_checklist": [
            f"Match your spray tip orifice to #{orifice_size:.1f} ($\\text{{GPM}} \\times \\sqrt{{4000 / \\text{{PSI}}}}$): using a smaller orifice forces water out the thermal unloader bypass, overheating pump seals.",
            f"Never exceed {ideal_sc_inches} to {ideal_sc_inches + 2} inches on your Rotary Surface Cleaner diameter for a {gpm} GPM pump; oversized decks spin slowly and leave circular 'tiger stripes' on driveways.",
            f"When replacing the dual nozzles underneath a 2-tip surface cleaner bar, divide your #{orifice_size:.1f} single-wand orifice in half (install two #{sc_tip_orifice:.2f} / {sc_tip_code} 25-degree MEG threaded tips).",
            "Purge all trapped air from your garden supply hose by squeezing the trigger gun for 30 seconds BEFORE starting the engine to prevent dry-start ceramic plunger cavitation."
        ],
        "faqs": [
            {
                "q": f"What size nozzle orifice do I need for the {model_name} ({psi:,} PSI / {gpm} GPM)?",
                "a": f"Using the Bernoulli orifice equation (Orifice = {gpm} GPM × √(4000 ÷ {psi} PSI)), your exact single-wand nozzle size is #{orifice_size:.1f} (e.g., 150{int(round(orifice_size*10)):02d}, 250{int(round(orifice_size*10)):02d}, and 400{int(round(orifice_size*10)):02d} tips). To lower pressure to 2,500 PSI for wood decks or car washing, step up to a #{round(gpm * math.sqrt(4000.0 / 2500.0), 1)} orifice."
            },
            {
                "q": f"What is the best surface cleaner size for {gpm} GPM at {psi:,} PSI?",
                "a": f"Multiply your GPM ({gpm}) by 4 inches: a {ideal_sc_inches}-inch rotary surface cleaner is the ideal match. It should be equipped with two #{sc_tip_orifice:.2f} ({sc_tip_code}) 1/4-inch NPT threaded nozzles."
            },
            {
                "q": f"How much PSI do I lose through 100 feet of pressure washer hose at {gpm} GPM?",
                "a": f"At {gpm} GPM, a 100-foot 3/8-inch ID hose loses only ~{int(round(gpm * 28))} PSI to friction, whereas a narrow 1/4-inch ID hose loses over {int(round(gpm * 95))} PSI. Always run 3/8-inch steel-braided hose for runs over 50 feet."
            }
        ]
    }


def generate_washer_data(washer_tuple):
    if not GEMINI_API_KEY:
        return build_deterministic_washer_data(washer_tuple)

    model_name, psi, gpm, pump_type, hose_spec = washer_tuple
    det_fallback = build_deterministic_washer_data(washer_tuple)
    sp = det_fallback["specs"]

    prompt = f"""
You are a PWNA (Power Washers of North America) Certified Commercial Exterior Cleaning Engineer & Triplex Pump Specialist. Create an accurate 2026 nozzle orifice size, rotary surface cleaner diameter, and hose friction loss guide for: "{model_name}".
Baseline specs: Pressure={psi} PSI, Flow={gpm} GPM ({sp['cleaning_units']} Cleaning Units), Single Nozzle Orifice=#{sp['orifice_number']}, Surface Cleaner Diameter={sp['surface_cleaner_inches']} Inches (Dual {sp['surface_cleaner_tip_code']} Tips), Pump={pump_type}, Hose={hose_spec}.
Return ONLY a valid JSON object matching this exact schema:
{{
  "washer_name": "{model_name}",
  "pump_type": "{pump_type}",
  "seo_title": "{model_name} Orifice Nozzle, Surface Cleaner & PSI Calculator (2026)",
  "meta_description": "Calculate exact nozzle orifice size, rotary surface cleaner diameter, dual-tip MEG codes, and hose PSI loss for {model_name}.",
  "specs": {{
    "max_psi": {psi},
    "flow_gpm": {gpm},
    "cleaning_units": {sp['cleaning_units']},
    "orifice_number": {sp['orifice_number']},
    "surface_cleaner_inches": {sp['surface_cleaner_inches']},
    "surface_cleaner_tip_code": "{sp['surface_cleaner_tip_code']}",
    "wand_recoil_lbs": {sp['wand_recoil_lbs']},
    "pump_engine_spec": "{pump_type}",
    "hose_spec": "{hose_spec}"
  }},
  "fluid_verdict": "3-sentence technical summary stating PSI, GPM, Cleaning Units, exact single-wand orifice size, max surface cleaner diameter (4 inches per GPM rule), and dual-tip MEG nozzle codes.",
  "hardware_bundle": [
    {{
      "badge": "{psi} PSI / {gpm} GPM Unit",
      "title": "{model_name}",
      "price_range": "$389 - $1,399",
      "amazon_query": "{model_name} Pressure Washer",
      "wash_note": "1-sentence pump and engine performance note"
    }},
    {{
      "badge": "{sp['surface_cleaner_inches']}\" Surface Cleaner",
      "title": "{sp['surface_cleaner_inches']}-Inch Stainless Steel Rotary Surface Cleaner (Dual {sp['surface_cleaner_tip_code']} Tips)",
      "price_range": "$99 - $389",
      "amazon_query": "{sp['surface_cleaner_inches']} Inch Stainless Pressure Washer Surface Cleaner",
      "wash_note": "1-sentence 4-inch per GPM flatwork speed note"
    }},
    {{
      "badge": "#{sp['orifice_number']} Orifice & Injector",
      "title": "#{sp['orifice_number']} Orifice Nozzle Tip Set + High-Draw Downstream Chemical Injector",
      "price_range": "$29 - $79",
      "amazon_query": "Pressure Washer Nozzle Tips {sp['orifice_number']} Orifice Downstream Injector",
      "wash_note": "1-sentence unloader valve protection and soft-wash note"
    }},
    {{
      "badge": "100ft 3/8\" Braided Hose",
      "title": "100ft 3/8-Inch Non-Marking Steel-Braided High-Pressure Hose + Swivel Gun",
      "price_range": "$109 - $229",
      "amazon_query": "100ft 3/8 Non Marking Steel Braided Pressure Washer Hose",
      "wash_note": "1-sentence friction pressure loss reduction note"
    }}
  ],
  "operator_checklist": [
    "Step 1 regarding orifice formula (GPM * sqrt(4000 / PSI)) and unloader bypass",
    "Step 2 regarding 4-inch per GPM surface cleaner rule to prevent tiger striping",
    "Step 3 regarding splitting orifice in half for 2-nozzle surface cleaner bars",
    "Step 4 regarding purging garden hose air before engine startup"
  ],
  "faqs": [
    {{"q": "What size nozzle orifice do I need for the {model_name}?", "a": "Exact orifice number for full PSI and oversized orifice for low-pressure rinsing."}},
    {{"q": "What size surface cleaner can the {model_name} run?", "a": "Exact diameter in inches and dual MEG tip codes."}},
    {{"q": "What hose diameter should I use for 100ft runs on the {model_name}?", "a": "Exact PSI friction loss comparison between 1/4-inch and 3/8-inch hose."}}
  ]
}}
"""

    for model_id in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)
                if "specs" in parsed and "hardware_bundle" in parsed:
                    return parsed
        except Exception as e:
            print(f"[WARN] Gemini ({model_id}) notice for '{model_name}': {e}")

    return det_fallback


def build_washer_html_page(data, slug, mon_cfg):
    washer_name = data.get("washer_name", "Commercial Pressure Washer")
    sp = data.get("specs", {})
    psi = int(safe_float(sp.get("max_psi", 4000), 4000))
    gpm = round(safe_float(sp.get("flow_gpm", 4.0), 4.0), 1)
    cu = int(safe_float(sp.get("cleaning_units", int(psi * gpm)), 16000))
    orifice_num = round(safe_float(sp.get("orifice_number", 4.0), 4.0), 1)
    sc_in = int(safe_float(sp.get("surface_cleaner_inches", int(gpm * 4)), 16))
    sc_code = sp.get("surface_cleaner_tip_code", "25020")
    pump_spec = sp.get("pump_engine_spec", "Commercial Triplex Plunger")

    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Commercial+Pressure+Washer+Surface+Cleaner"), mon_cfg)

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": f"{washer_name} Orifice Nozzle & Surface Cleaner Calculator",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web Browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
                    } for f in data.get("faqs", [])
                ]
            }
        ]
    }

    bundle_html = ""
    for item in data.get("hardware_bundle", []):
        amz_url = build_amazon_url(item.get("amazon_query", item.get("title", "Pressure Washer Surface Cleaner")), mon_cfg)
        bundle_html += f"""
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-blue-500/60 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2.5 py-0.5 rounded">{item.get('badge', 'Wash Gear')}</span>
              <span class="text-sm font-bold text-emerald-400">{item.get('price_range', '$79+')}</span>
            </div>
            <h3 class="text-base font-bold text-white mt-2">{item.get('title', '')}</h3>
            <p class="text-xs text-slate-400 mt-2 leading-relaxed">💦 {item.get('wash_note', '')}</p>
          </div>
          <a href="{amz_url}" target="_blank" rel="nofollow sponsored" class="mt-5 block text-center bg-blue-500 hover:bg-blue-400 text-slate-950 font-extrabold py-2.5 px-4 rounded-lg text-sm transition shadow-lg">
            Check Price on Amazon →
          </a>
        </div>"""

    # Build GPM vs Orifice & Surface Cleaner Reference Matrix Table
    gpm_tiers = [
        ("2.0 GPM @ 2,000 PSI", "#2.8 Orifice", "8\" – 12\" Surface Cleaner", "2x #1.5 (25015 Tips)", "4,000 CU"),
        ("2.5 GPM @ 3,200 PSI", "#2.8 Orifice", "12\" – 14\" Surface Cleaner", "2x #1.5 (25015 Tips)", "8,000 CU"),
        ("3.0 GPM @ 3,500 PSI", "#3.2 Orifice", "14\" – 15\" Surface Cleaner", "2x #1.6 (25015 Tips)", "10,500 CU"),
        ("3.5 GPM @ 3,800 PSI", "#3.6 Orifice", "15\" – 16\" Surface Cleaner", "2x #1.8 (25020 Tips)", "13,300 CU"),
        ("4.0 GPM @ 4,200 PSI", "#3.9 / #4.0 Orifice", "16\" – 20\" Surface Cleaner", "2x #2.0 (25020 Tips)", "16,800 CU"),
        ("5.5 GPM @ 3,500 PSI", "#5.9 / #6.0 Orifice", "20\" – 24\" Surface Cleaner", "2x #3.0 (25030 Tips)", "19,250 CU")
    ]
    matrix_rows_html = ""
    for g_lbl, or_lbl, sc_lbl, tip_lbl, cu_lbl in gpm_tiers:
        matrix_rows_html += f"""
        <tr class="border-b border-slate-800 hover:bg-slate-800/40">
          <td class="py-3 px-4 font-bold text-white">{g_lbl}</td>
          <td class="py-3 px-4 font-bold text-blue-400">{or_lbl}</td>
          <td class="py-3 px-4 text-emerald-400 font-semibold">{sc_lbl}</td>
          <td class="py-3 px-4 text-slate-300">{tip_lbl}</td>
          <td class="py-3 px-4 text-xs text-slate-400">{cu_lbl}</td>
        </tr>"""

    checklist_html = ""
    for idx, step_text in enumerate(data.get("operator_checklist", []), start=1):
        checklist_html += f"""
        <label class="flex items-start gap-3.5 bg-slate-900 border border-slate-800 rounded-xl p-4 cursor-pointer hover:border-slate-700 transition">
          <input type="checkbox" class="mt-1 w-5 h-5 accent-blue-500 rounded cursor-pointer wash-check">
          <span class="text-sm text-slate-200 leading-relaxed"><strong>PWNA Step {idx}:</strong> {step_text}</span>
        </label>"""

    faqs_html = "".join([
        f"<div class='bg-slate-900 border border-slate-800 rounded-xl p-5'><h3 class='font-bold text-white text-base mb-2'>{f.get('q', '')}</h3><p class='text-sm text-slate-300 leading-relaxed'>{f.get('a', '')}</p></div>"
        for f in data.get("faqs", [])
    ])

    canonical_url = f"{SITE_BASE_URL}/{slug}.html"
    amz_domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    amz_tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data.get('seo_title', washer_name)}</title>
  <meta name="description" content="{data.get('meta_description', '')}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{data.get('seo_title', washer_name)}">
  <meta property="og:description" content="{data.get('meta_description', '')}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{json.dumps(schema_graph)}</script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen flex flex-col">
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-30">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <a href="index.html" class="text-lg font-black tracking-tight text-white flex items-center gap-2">
        <span class="bg-blue-500 text-slate-950 px-2 py-0.5 rounded font-black">ORIFICE</span>WashIndex
      </a>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-blue-500 hover:bg-blue-400 text-slate-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Pressure Washers & Surface Cleaners →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-10 flex-1 w-full">
    <div class="mb-8">
      <div class="flex flex-wrap items-center gap-2.5 mb-3">
        <span class="text-xs font-extrabold uppercase tracking-widest bg-blue-500 text-slate-950 px-3 py-1 rounded-full">{psi:,} PSI | {gpm} GPM ({cu:,} CU)</span>
        <span class="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">Nozzle: #{orifice_num:.1f} Orifice | Surface Cleaner: {sc_in}"</span>
        <span class="text-xs font-semibold bg-slate-800 text-slate-300 px-3 py-1 rounded-full">{pump_spec} | Dual {sc_code} Tips</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white leading-tight">{data.get('seo_title', washer_name)}</h1>
      <div class="mt-4 bg-slate-900 border-l-4 border-blue-500 p-4 rounded-r-xl text-sm text-slate-200 leading-relaxed">
        <strong>PWNA Fluid & Orifice Sizing Verdict:</strong> {data.get('fluid_verdict', '')}
      </div>
    </div>

    <!-- INTERACTIVE ORIFICE NOZZLE, SURFACE CLEANER & HOSE PSI LOSS CALCULATOR -->
    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 mb-12 shadow-2xl">
      <h2 class="text-xl font-extrabold text-white mb-2">Interactive {washer_name} Nozzle & Surface Cleaner Calculator</h2>
      <p class="text-xs text-slate-400 mb-6">Adjust your pump GPM flow rate, target nozzle PSI, and high-pressure hose length/diameter to calculate exact orifice nozzle number, max surface cleaner diameter, and net PSI at the gun.</p>

      <div class="grid md:grid-cols-2 gap-8 items-center">
        <div class="space-y-5">
          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="gpmSlider" class="text-slate-300">Pump Flow Rate (Gallons Per Minute - GPM)</label>
              <span class="text-blue-400 font-bold"><span id="gpmVal">{gpm}</span> GPM</span>
            </div>
            <input id="gpmSlider" type="range" min="1.5" max="8.5" step="0.1" value="{gpm}" class="w-full accent-blue-500 cursor-pointer">
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="psiSlider" class="text-slate-300">Target Operating Pressure at Tip (PSI)</label>
              <span class="text-blue-400 font-bold"><span id="psiVal">{psi:,}</span> PSI</span>
            </div>
            <input id="psiSlider" type="range" min="1000" max="4500" step="100" value="{psi}" class="w-full accent-blue-500 cursor-pointer">
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="hoseLenSelect" class="block text-xs font-medium text-slate-400 mb-1">High-Pressure Hose Length</label>
              <select id="hoseLenSelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                <option value="50">50 Feet Hose</option>
                <option value="100" selected>100 Feet Hose</option>
                <option value="150">150 Feet Hose</option>
                <option value="200">200 Feet Commercial Reel</option>
              </select>
            </div>
            <div>
              <label for="hoseDiaSelect" class="block text-xs font-medium text-slate-400 mb-1">Hose Inner Diameter (ID)</label>
              <select id="hoseDiaSelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                <option value="95">1/4" Consumer Hose (High Loss)</option>
                <option value="28" selected>3/8" Commercial Braided</option>
                <option value="9">1/2" High-Flow Rig Hose</option>
              </select>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-slate-950 border border-blue-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-blue-400 font-bold">Required Nozzle Orifice</span>
            <div class="text-2xl sm:text-3xl font-black text-white mt-1">#<span id="orificeOut">{orifice_num:.1f}</span> <span class="text-xs font-normal text-slate-400">Tip</span></div>
            <p id="dualTipOut" class="text-xs text-blue-400 font-semibold mt-1">2-Tip Bar: 2x #{orifice_num/2:.2f} ({sc_code})</p>
          </div>

          <div class="bg-slate-950 border border-emerald-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-emerald-400 font-bold">Max Surface Cleaner</span>
            <div class="text-2xl sm:text-3xl font-black text-emerald-400 mt-1"><span id="scDiaOut">{sc_in}</span>" <span class="text-xs font-normal text-slate-400">Deck</span></div>
            <p id="psiLossOut" class="text-xs text-slate-300 font-semibold mt-1">Hose Loss: -110 PSI</p>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-blue-950/40 border border-blue-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div id="washAdviceBanner" class="text-sm text-blue-100 font-medium"></div>
        <a id="dynamicWashBtn" href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="shrink-0 bg-blue-500 hover:bg-blue-400 text-slate-950 font-extrabold px-4 py-2.5 rounded-lg text-xs uppercase tracking-wider transition">
          Shop Matched Surface Cleaner & Tips on Amazon →
        </a>
      </div>
    </section>

    <!-- 4-CARD HARDWARE BUNDLE -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Complete {washer_name} Surface Cleaner, Hose & Nozzle Kit</h2>
        <span class="text-xs text-slate-400">4,500 PSI Commercial Quick-Connect Rated</span>
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{bundle_html}</div>
    </section>

    <!-- GPM & ORIFICE MATRIX TABLE -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-4">Pressure Washer GPM, Nozzle Orifice # & Surface Cleaner Sizing Chart</h2>
      <div class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-xl">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase text-xs">
              <th class="py-3.5 px-4">Washer Flow & Pressure</th>
              <th class="py-3.5 px-4 text-blue-400">Single Wand Orifice</th>
              <th class="py-3.5 px-4 text-emerald-400">Max Surface Cleaner</th>
              <th class="py-3.5 px-4">2-Nozzle Bar Tips</th>
              <th class="py-3.5 px-4">Cleaning Units</th>
            </tr>
          </thead>
          <tbody>{matrix_rows_html}</tbody>
        </table>
      </div>
    </section>

    <!-- OPERATOR CHECKLIST -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">PWNA Commercial Flatwork & Pump Protection Checklist</h2>
        <span id="washBadge" class="text-xs font-bold bg-slate-800 text-blue-400 px-3 py-1 rounded-full">0 / 4 Completed</span>
      </div>
      <div class="space-y-3">{checklist_html}</div>
    </section>

    <!-- FAQ -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-5">Frequently Asked Questions ({washer_name})</h2>
      <div class="space-y-4">{faqs_html}</div>
    </section>
  </main>

  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500 px-4">
    <p>© {datetime.now(timezone.utc).year} OrificeWashIndex. Independent Pressure Washer Hydraulics & Orifice Sizing Database. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const amzDomain = "{amz_domain}";
    const amzTag = "{amz_tag}";

    const gpmSlider = document.getElementById('gpmSlider');
    const psiSlider = document.getElementById('psiSlider');
    const hoseLenSelect = document.getElementById('hoseLenSelect');
    const hoseDiaSelect = document.getElementById('hoseDiaSelect');
    const gpmVal = document.getElementById('gpmVal');
    const psiVal = document.getElementById('psiVal');
    const orificeOut = document.getElementById('orificeOut');
    const dualTipOut = document.getElementById('dualTipOut');
    const scDiaOut = document.getElementById('scDiaOut');
    const psiLossOut = document.getElementById('psiLossOut');
    const washAdviceBanner = document.getElementById('washAdviceBanner');
    const dynamicWashBtn = document.getElementById('dynamicWashBtn');

    function recalculateWasher() {{
      const gpm = parseFloat(gpmSlider.value);
      const psi = parseInt(psiSlider.value, 10);
      const hoseLen = parseInt(hoseLenSelect.value, 10);
      const lossFactorPer100 = parseInt(hoseDiaSelect.value, 10);

      gpmVal.textContent = gpm.toFixed(1);
      psiVal.textContent = psi.toLocaleString();

      const rawOrifice = gpm * Math.sqrt(4000.0 / psi);
      const stdOrifice = (Math.round(rawOrifice * 2.0) / 2.0).toFixed(1);
      const halfOrifice = (rawOrifice / 2.0).toFixed(2);
      const megCode = "250" + Math.round((rawOrifice / 2.0) * 10).toString().padStart(2, '0');

      const maxScIn = Math.round(gpm * 4.0);
      const psiDrop = Math.round(gpm * lossFactorPer100 * (hoseLen / 100.0));
      const cleanUnits = Math.round(gpm * psi);

      orificeOut.textContent = stdOrifice;
      dualTipOut.textContent = `2-Tip Bar: 2x #${{halfOrifice}} (${{megCode}})`;
      scDiaOut.textContent = maxScIn;
      psiLossOut.textContent = `Hose Loss: -${{psiDrop}} PSI (${{cleanUnits.toLocaleString()}} CU)`;

      washAdviceBanner.innerHTML = `💦 <strong>PWNA Flatwork Spec:</strong> At <strong>${{gpm.toFixed(1)}} GPM / ${{psi.toLocaleString()}} PSI</strong>, run a <strong>#${{stdOrifice}} Orifice Nozzle Set</strong> and a <strong>${{maxScIn}}-Inch Rotary Surface Cleaner</strong> (fitted with two ${{megCode}} MEG tips).`;
      dynamicWashBtn.href = `https://${{amzDomain}}/s?k=${{maxScIn}}+Inch+Pressure+Washer+Surface+Cleaner+${{stdOrifice}}+Orifice+Nozzle+Tips&tag=${{amzTag}}`;
    }}

    gpmSlider.addEventListener('input', recalculateWasher);
    psiSlider.addEventListener('input', recalculateWasher);
    hoseLenSelect.addEventListener('change', recalculateWasher);
    hoseDiaSelect.addEventListener('change', recalculateWasher);
    recalculateWasher();

    const checks = document.querySelectorAll('.wash-check');
    const badge = document.getElementById('washBadge');
    checks.forEach(ch => {{
      ch.addEventListener('change', () => {{
        const done = Array.from(checks).filter(c => c.checked).length;
        badge.textContent = `${{done}} / ${{checks.length}} Completed`;
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)


def rebuild_portal_sitemap_and_rss(published, mon_cfg):
    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Commercial+Pressure+Washer+Surface+Cleaner"), mon_cfg)

    cards_html = ""
    for item in reversed(published):
        cards_html += f"""
        <a href="{item['slug']}.html" class="block bg-slate-900 border border-slate-800 hover:border-blue-500/60 rounded-xl p-5 transition group">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-black uppercase bg-blue-500 text-slate-950 px-2.5 py-0.5 rounded">{item.get('psi', 4000):,} PSI | {item.get('gpm', 4.0)} GPM</span>
            <span class="text-xs text-slate-400">#{item.get('orifice', 4.0)} Orifice | {item.get('sc_in', 16)}" Cleaner</span>
          </div>
          <h2 class="text-base font-bold text-white group-hover:text-blue-400 transition">{item['washer_name']}</h2>
          <p class="text-xs text-slate-400 mt-2 line-clamp-2">{item['description']}</p>
          <span class="inline-block mt-4 text-xs font-extrabold text-blue-400">Calculate Orifice # & Surface Cleaner →</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OrificeWashIndex — Pressure Washer Orifice Nozzle, Surface Cleaner & PSI Calculator (2026)</title>
  <meta name="description" content="Calculate exact pressure washer nozzle orifice size (#2.5–#6.0), rotary surface cleaner diameter (4 inches per GPM rule), and hose PSI friction loss for Simpson, DeWalt, Honda GX390, Predator, and CAT Pump setups.">
  <link rel="canonical" href="{SITE_BASE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="OrificeWashIndex RSS Feed" href="{SITE_BASE_URL}/rss.xml">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">
  <header class="border-b border-slate-800 bg-slate-900/80 sticky top-0 z-30 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <div class="text-lg font-black text-white flex items-center gap-2">
        <span class="bg-blue-500 text-slate-950 px-2 py-0.5 rounded font-black">ORIFICE</span>WashIndex
      </div>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-blue-500 hover:bg-blue-400 text-slate-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Pressure Washers & Surface Cleaners →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-12 flex-1 w-full">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <h1 class="text-3xl sm:text-5xl font-black text-white tracking-tight">Pressure Washer Orifice Nozzle & Surface Cleaner Database</h1>
      <p class="text-slate-400 mt-3 text-base sm:text-lg">Select your pressure washer model or GPM/PSI rating below to calculate exact spray tip orifice numbers, maximum rotary surface cleaner width, and 100ft hose pressure loss.</p>
      <div class="mt-6">
        <input id="filterInput" type="text" placeholder="Search washer model or GPM (e.g. Simpson PowerShot 4200, DeWalt 3800, Predator 4400, 4.0 GPM, CAT Pump...)" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-blue-500">
      </div>
    </div>

    <div id="washGrid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards_html}</div>
  </main>

  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500">
    <p>© {datetime.now(timezone.utc).year} OrificeWashIndex. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    const cards = Array.from(document.getElementById('washGrid').children);
    filterInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.textContent.toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in published:
        urls_xml += f"""  <url>
    <loc>{SITE_BASE_URL}/{item['slug']}.html</loc>
    <lastmod>{item.get('date', today)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>""")

    rss_items = ""
    for item in list(reversed(published))[:30]:
        rss_items += f"""    <item>
      <title>{item['title']}</title>
      <link>{SITE_BASE_URL}/{item['slug']}.html</link>
      <guid>{SITE_BASE_URL}/{item['slug']}.html</guid>
      <description>{item['description']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>OrificeWashIndex Pressure Washer & Surface Cleaner Database</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Interactive Pressure Washer Orifice Nozzle, Surface Cleaner & PSI Calculators</description>
    <atom:link href="{SITE_BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
{rss_items}  </channel>
</rss>"""

    with open(os.path.join(DOCS_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def notify_search_engines(new_urls):
    if not SITE_BASE_URL or not new_urls:
        return
    parsed_host = urllib.parse.urlparse(SITE_BASE_URL).netloc
    payload = {
        "host": parsed_host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls
    }
    try:
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[INDEXNOW] Pushed {len(new_urls)} URLs (HTTP {resp.status})")
    except Exception as e:
        print(f"[WARN] IndexNow ping notice: {e}")

    try:
        hub_data = urllib.parse.urlencode({
            "hub.mode": "publish",
            "hub.url": f"{SITE_BASE_URL}/rss.xml"
        }).encode("utf-8")
        req_hub = urllib.request.Request(
            "https://pubsubhubbub.appspot.com/",
            data=hub_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req_hub, timeout=15) as resp_hub:
            print(f"[WEBSUB] Google PubSubHubbub ping status: {resp_hub.status}")
    except Exception as e:
        print(f"[WARN] WebSub ping notice: {e}")


def main():
    published = load_json(PUBLISHED_FILE, [])
    mon_cfg = load_json(MONETIZATION_FILE, {})
    published_slugs = {item["slug"] for item in published}

    candidates = []
    if CUSTOM_WASHER:
        candidates.append((CUSTOM_WASHER.strip(), 4000, 4.0, "Commercial Triplex Plunger", "3/8-Inch QC"))
    candidates.extend(SEED_WASHERS)
    candidates.extend(discover_google_washer_queries())

    new_urls = []
    count = 0

    for washer_tuple in candidates:
        if count >= PAGES_PER_RUN:
            break
        w_name = washer_tuple[0]
        slug = slugify(f"{w_name}-nozzle-surface-cleaner-calculator")
        if slug in published_slugs:
            continue

        print(f"[ENGINE] Generating pressure washer orifice & surface cleaner calculator for: {w_name}...")
        try:
            data = generate_washer_data(washer_tuple)
            build_washer_html_page(data, slug, mon_cfg)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sp = data.get("specs", {})

            published.append({
                "washer_name": data.get("washer_name", w_name),
                "slug": slug,
                "title": data.get("seo_title", f"{w_name} Nozzle Calculator"),
                "description": data.get("meta_description", ""),
                "psi": int(safe_float(sp.get("max_psi", washer_tuple[1]), washer_tuple[1])),
                "gpm": round(safe_float(sp.get("flow_gpm", washer_tuple[2]), washer_tuple[2]), 1),
                "orifice": round(safe_float(sp.get("orifice_number", 4.0), 4.0), 1),
                "sc_in": int(safe_float(sp.get("surface_cleaner_inches", 16), 16)),
                "date": today
            })
            published_slugs.add(slug)
            if SITE_BASE_URL:
                new_urls.append(f"{SITE_BASE_URL}/{slug}.html")
            count += 1
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Failed building {w_name}: {e}")

    save_json(PUBLISHED_FILE, published)
    rebuild_portal_sitemap_and_rss(published, mon_cfg)
    if new_urls and SITE_BASE_URL:
        new_urls.append(f"{SITE_BASE_URL}/")
        notify_search_engines(new_urls)
    print(f"[DONE] Published {count} new pressure washer nozzle & surface cleaner calculator pages.")


if __name__ == "__main__":
    main()
