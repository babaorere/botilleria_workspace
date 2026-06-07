from __future__ import annotations

import re


class BotilleriaSpellCorrector:
    # Dictionary of standard categories mapped to common typos, singular/plural variations
    DICT = {
        "Cervezas": [
            "cerveza",
            "cervesa",
            "serveza",
            "serbesa",
            "cerbesa",
            "chela",
            "chelas",
        ],
        "Destilados": [
            "destilado",
            "distilado",
            "distilados",
            "destilaos",
            "piscos",
            "pisos",
        ],
        "Vinos": ["vino", "bino", "vinos", "binos", "tintos", "tinto"],
        "Bebidas": ["bebida", "bevida", "bebidas", "bevidas", "gaseosas", "gaseosa"],
        "Snacks": ["snack", "snacks", "esnak", "esnaks", "esnac", "esnacs", "papas"],
        "Licores": ["licor", "licores", "likor", "likores", "trago", "tragos"],
    }

    @classmethod
    def correct(cls, text: str) -> str:
        if not text:
            return ""

        cleaned = text.strip().lower()
        # Remove extra spaces
        cleaned = re.sub(r"\s+", " ", cleaned)

        # Check direct dictionary matches
        for category, variations in cls.DICT.items():
            if cleaned == category.lower():
                return category
            for var in variations:
                if cleaned == var:
                    return category

        # Check substring matches
        for category, variations in cls.DICT.items():
            if cleaned in category.lower() or category.lower() in cleaned:
                return category
            for var in variations:
                if var in cleaned or cleaned in var:
                    return category

        # Clean capitalization and spaces if no match
        return text.strip().title()


class KBSpellCorrector:
    DICT = {
        "General": ["gral", "general", "comun", "básico"],
        "Delivery": [
            "envio",
            "envios",
            "despacho",
            "despachos",
            "reparto",
            "repartos",
            "domicilio",
        ],
        "Horarios": [
            "horario",
            "horarios",
            "hora",
            "horas",
            "atencion",
            "abierto",
            "cerrado",
        ],
        "Metodos de Pago": [
            "pago",
            "pagos",
            "transferencia",
            "efectivo",
            "tarjeta",
            "tarjetas",
            "redcompra",
        ],
        "Ubicacion": [
            "ubicacion",
            "direccion",
            "donde",
            "donde estan",
            "donde queda",
            "mapa",
        ],
        "Contacto": [
            "contacto",
            "telefono",
            "whatsapp",
            "fono",
            "email",
            "correo",
            "instagram",
        ],
        "Stock y Pedidos": [
            "stock",
            "pedidos",
            "pedido",
            "compras",
            "compra",
            "mayorista",
        ],
        "Devoluciones": ["devolucion", "devoluciones", "cambio", "cambios", "garantia"],
        "Precios y Ofertas": [
            "precio",
            "precios",
            "oferta",
            "ofertas",
            "descuento",
            "descuentos",
            "promo",
            "promos",
        ],
        "Eventos": [
            "evento",
            "eventos",
            "fiesta",
            "fiestas",
            "barril",
            "barriles",
            "shoperas",
        ],
        "Reclamos": [
            "reclamo",
            "reclamos",
            "queja",
            "quejas",
            "sugerencia",
            "sugerencias",
        ],
    }

    @classmethod
    def correct(cls, text: str) -> str:
        if not text:
            return ""

        cleaned = text.strip().lower()
        cleaned = re.sub(r"\s+", " ", cleaned)

        # Check direct dictionary matches
        for category, variations in cls.DICT.items():
            if cleaned == category.lower():
                return category
            for var in variations:
                if cleaned == var:
                    return category

        # Check substring matches
        for category, variations in cls.DICT.items():
            if cleaned in category.lower() or category.lower() in cleaned:
                return category
            for var in variations:
                if var in cleaned or cleaned in var:
                    return category

        return text.strip().title()
