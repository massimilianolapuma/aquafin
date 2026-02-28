"""Predefined Italian categories for seeding the database."""

from __future__ import annotations

# Each entry: (name_key, icon, color, is_income, children)
# Children is a list of (name_key, icon, color) tuples.

SYSTEM_CATEGORIES: list[tuple[str, str, str, bool, list[tuple[str, str, str]]]] = [
    # ── Expense categories ──────────────────────────────────────────────
    (
        "Alimentari",
        "🛒",
        "#4CAF50",
        False,
        [
            ("Supermercato", "🏪", "#66BB6A"),
            ("Ristorante", "🍽️", "#81C784"),
            ("Bar/Caffè", "☕", "#A5D6A7"),
            ("Delivery", "🛵", "#C8E6C9"),
        ],
    ),
    (
        "Casa",
        "🏠",
        "#2196F3",
        False,
        [
            ("Affitto/Mutuo", "🔑", "#42A5F5"),
            ("Utenze", "💡", "#64B5F6"),
            ("Manutenzione", "🔧", "#90CAF9"),
            ("Assicurazione casa", "🛡️", "#BBDEFB"),
        ],
    ),
    (
        "Trasporti",
        "🚗",
        "#FF9800",
        False,
        [
            ("Carburante", "⛽", "#FFA726"),
            ("Trasporto pubblico", "🚌", "#FFB74D"),
            ("Parcheggio", "🅿️", "#FFCC80"),
            ("Manutenzione auto", "🔩", "#FFE0B2"),
            ("Assicurazione auto", "📋", "#FFF3E0"),
        ],
    ),
    (
        "Salute",
        "❤️",
        "#F44336",
        False,
        [
            ("Farmacia", "💊", "#EF5350"),
            ("Visite mediche", "🩺", "#E57373"),
            ("Dentista", "🦷", "#EF9A9A"),
        ],
    ),
    (
        "Shopping",
        "🛍️",
        "#9C27B0",
        False,
        [
            ("Abbigliamento", "👕", "#AB47BC"),
            ("Elettronica", "📱", "#BA68C8"),
            ("Casa e arredo", "🪑", "#CE93D8"),
        ],
    ),
    (
        "Svago",
        "🎉",
        "#E91E63",
        False,
        [
            ("Cinema/Teatro", "🎬", "#EC407A"),
            ("Sport", "⚽", "#F06292"),
            ("Viaggi", "✈️", "#F48FB1"),
            ("Hobby", "🎨", "#F8BBD0"),
        ],
    ),
    (
        "Servizi",
        "📡",
        "#00BCD4",
        False,
        [
            ("Telefonia", "📞", "#26C6DA"),
            ("Internet", "🌐", "#4DD0E1"),
            ("Abbonamenti", "📺", "#80DEEA"),
            ("Software", "💻", "#B2EBF2"),
        ],
    ),
    (
        "Finanza",
        "🏦",
        "#607D8B",
        False,
        [
            ("Commissioni bancarie", "💳", "#78909C"),
            ("Tasse", "📄", "#90A4AE"),
            ("Consulenza", "📊", "#B0BEC5"),
        ],
    ),
    (
        "Istruzione",
        "🎓",
        "#795548",
        False,
        [
            ("Corsi", "📚", "#8D6E63"),
            ("Libri", "📖", "#A1887F"),
            ("Materiale", "✏️", "#BCAAA4"),
        ],
    ),
    (
        "Altro spese",
        "📦",
        "#9E9E9E",
        False,
        [],
    ),
    # ── Income categories ───────────────────────────────────────────────
    (
        "Stipendio",
        "💰",
        "#4CAF50",
        True,
        [],
    ),
    (
        "Freelance",
        "💼",
        "#8BC34A",
        True,
        [],
    ),
    (
        "Investimenti",
        "📈",
        "#009688",
        True,
        [
            ("Dividendi", "💵", "#26A69A"),
            ("Interessi", "🏧", "#4DB6AC"),
            ("Plusvalenze", "📊", "#80CBC4"),
        ],
    ),
    (
        "Rimborsi",
        "🔄",
        "#03A9F4",
        True,
        [],
    ),
    (
        "Regali",
        "🎁",
        "#FF5722",
        True,
        [],
    ),
    (
        "Altro entrate",
        "📥",
        "#9E9E9E",
        True,
        [],
    ),
]
