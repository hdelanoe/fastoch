from django.test import TestCase
import json
from inventory.models import Inventory, Product, StockTransaction, Kesia2_column_names


class InventoryTestCase(TestCase):
    def setUp(self):
        Inventory.create(name='testInventory')

    def serialize_json(self):

        str = '''
            [
        {
            "fournisseur": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770007175687",
            "description": "Indian Pale Ale bio 75 cl - 5.5 % alc. - Bière de Besançon",
            "quantity": 6,
            "achat_brut": 4.20,
            "achat_tva": 0.48,      "achat_net": 4.68
        },
        {
            "fournisseur": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770007175021",
            "description": "Rousse Bisonquine Bio - 75 cl - Bière de Besançon",
            "quantity": 12,
            "achat_brut": 4.10,
            "achat_tva": 0.45,      "achat_net": 4.55
        },
        {
            "fournisseur": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770007175038",
            "description": "Bisonquine Classique Bio - 75 cl Bière de Besançon - Type Pilsen",
            "quantity": 15,
            "achat_brut": 3.72,
            "achat_tva": 0.40,      "achat_net": 4.12
        },
        {
            "fournisseur": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770007175038",
            "description": "Bisonquine Classique Bio - 75 cl Bière de Besançon - Type Pilsen",
            "quantity": 15,
            "achat_brut": 3.72,
            "achat_tva": 0.40,      "achat_net": 4.12
        },
        {
            "fournisseur": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770 007 175 540",
            "description": "Douce Bisonquine bio - 75cl Bière de Besançon - 1.8 % alc.",
            "quantity": 15,
            "achat_brut": 3.50,
            "achat_tva": 0.38,      "achat_net": 3.88
        },
        {
            "fournisseur": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770 007 175 540",
            "description": "Douce Bisonquine bio - 75cl Bière de Besançon - 1.8 % alc.",
            "quantity": 15,
            "achat_brut": 3.50,
            "achat_tva": 0.38,      "achat_net": 3.88
        }
    ]
            '''
        
        json_data = json.loads(str)
        inventory = Inventory.get('testInventory')
        for jd in json_data:
            product = Product.objects.create(
                fournisseur=jd.get('fournisseur'),
                ean=jd.get('ean'),
                description=jd.get('description'),
                quantity=jd.get('quantity'),
                achat_tva=jd.get('achat_tva'),
                achat_net=jd.get('achat_net'),
            )
            product.save()
            transaction = StockTransaction.objects.create(
                product=product,
                quantity=product.quantity
            )
            transaction.save()
            inventory.products.add(product)
            inventory.transaction_list.add(transaction)
        inventory.save()
        self.assertEqual(6, len(inventory.transaction_list.all()))


