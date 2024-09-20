class Column_Parser():
    ean = [
        "EAN", # Vitafrais
        "Code EAN", # GANGLOFF
    ]
    quantity = [
        "Nb Colis / Pièce", # Pronatura
        "Qté", # Brasserie Ad LIBITUM, Vitafrais, GANGLOFF
        "Qté\ntotale", # AQUIBIO
    ]
    description = [
        "Désignation",  # Pronatura
        "Produit",  # Brasserie Ad LIBITUM, AQUIBIO
    ]
    price_achat_HT = [
        "Prix",  # Pronatura
        "P.U. HT",  # Pronatura, AQUIBIO
        "PU HT",  # Vitafrais
        "Prix U. HT",  # GANGLOFF
    ]
    price_achat = [
        "Prix Net",  # Pronatura
    ]
    tva_achat = [
        "%\nTVA",  # Pronatura
        "% TVA",  # Pronatura, Brasserie Ad LIBITUM
    ]
    weight = [
        "Poids net / brut", # Pronatura
    ]
    unit = [
        "U", # Pronatura
    ]

    def __description__(self, desc):
        for d in self.description:
            if d == desc:
                return desc
            return ""

def table_to_product():
    return None
        
