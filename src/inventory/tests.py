from django.test import TestCase
import json
from inventory.models import Inventory, Product, Transaction
from inventory.views import json_to_db


class InventoryTestCase(TestCase):
    def setUp(self):
        Inventory.create(name='testInventory')

    def serialize_json(self):

        str = '''
            [
        {
            "provider": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770007175687",
            "description": "Indian Pale Ale bio 75 cl - 5.5 % alc. - Bière de Besançon",
            "quantity": 6,
            "achat_ht": 4.20,
            "achat_tva": 0.48,      "achat_net": 4.68
        },
        {
            "provider": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770007175021",
            "description": "Rousse Bisonquine Bio - 75 cl - Bière de Besançon",
            "quantity": 12,
            "achat_ht": 4.10,
            "achat_tva": 0.45,      "achat_net": 4.55
        },
        {
            "provider": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770007175038",
            "description": "Bisonquine Classique Bio - 75 cl Bière de Besançon - Type Pilsen",
            "quantity": 15,
            "achat_ht": 3.72,
            "achat_tva": 0.40,      "achat_net": 4.12
        },
        {
            "provider": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770007175038",
            "description": "Bisonquine Classique Bio - 75 cl Bière de Besançon - Type Pilsen",
            "quantity": 15,
            "achat_ht": 3.72,
            "achat_tva": 0.40,      "achat_net": 4.12
        },
        {
            "provider": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770 007 175 540",
            "description": "Douce Bisonquine bio - 75cl Bière de Besançon - 1.8 % alc.",
            "quantity": 15,
            "achat_ht": 3.50,
            "achat_tva": 0.38,      "achat_net": 3.88
        },
        {
            "provider": "GANCLOFF BRASSERIE ARTISANALE SARL",
            "ean": "3770 007 175 540",
            "description": "Douce Bisonquine bio - 75cl Bière de Besançon - 1.8 % alc.",
            "quantity": 15,
            "achat_ht": 3.50,
            "achat_tva": 0.38,      "achat_net": 3.88
        }
    ]
            '''
        
        json_data = json.loads(str)
        inventory = Inventory.get('testInventory')
        for jd in json_data:
            product = Product.objects.create(
                provider=jd.get('provider'),
                ean=jd.get('ean'),
                description=jd.get('description'),
                quantity=jd.get('quantity'),
                achat_tva=jd.get('achat_tva'),
                achat_net=jd.get('achat_net'),
            )
            product.save()
            transaction = Transaction.objects.create(
                product=product,
                quantity=product.quantity
            )
            transaction.save()
            inventory.products.add(product)
            inventory.transactions.add(transaction)
        inventory.save()
        self.assertEqual(6, len(inventory.transactions.all()))

    def jsonToDBTestCase(self):
        str = '''
[
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "37600995302186776",
        "description": "Mozzarella di Bufala 125 g",
        "quantity": 8,
        "achat_ht": 1.000,
        "achat_tva": 2.02
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3252920039395",
        "description": "Mousse au chocolat noir 100 g",
        "quantity": 6,
        "achat_ht": 0.800,
        "achat_tva": 2.40
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "2746203",
        "description": "Fromage à l'ail des ours 4kg",
        "quantity": 1,
        "achat_ht": 4.820,
        "achat_tva": 16.30
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "376009953737364",
        "description": "Crevettes nature 100 g",
        "quantity": 4,
        "achat_ht": 0.400,
        "achat_tva": 4.19
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760099532413",
        "description": "Pâte feuilletée 250 g",
        "quantity": 6,
        "achat_ht": 1.360,
        "achat_tva": 1.31
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "4026584143502",
        "description": "Bouchées méditerranéennes",
        "quantity": 5,
        "achat_ht": 1.200,
        "achat_tva": 2.46
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "4026584142222",
        "description": "Mini roux primeurs sauce",
        "quantity": 6,
        "achat_ht": 1.200,
        "achat_tva": 2.58
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3175681262621",
        "description": "Falaffels condrires menthe",
        "quantity": 6,
        "achat_ht": 1.500,
        "achat_tva": 3.81
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760099532088",
        "description": "Lait entier stérilisé UHT 1 L",
        "quantity": 6,
        "achat_ht": 6.000,
        "achat_tva": 1.52
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760099539551",
        "description": "Lait 1/2 écrémé UHT 1 L",
        "quantity": 6,
        "achat_ht": 6.000,
        "achat_tva": 1.25
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3275221115580",
        "description": "Bouillon avocat nature UHT",
        "quantity": 6,
        "achat_ht": 0.208,
        "achat_tva": 1.97
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760095300018",
        "description": "Bouillon soja nature 1 L",
        "quantity": 6,
        "achat_ht": 0.500,
        "achat_tva": 1.44
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "5200104190964",
        "description": "Hummous d'olives noires",
        "quantity": 6,
        "achat_ht": 1.760,
        "achat_tva": 9.01
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3263670033458",
        "description": "Thon au naturel 112 g",
        "quantity": 12,
        "achat_ht": 1.920,
        "achat_tva": 3.53
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760346021165",
        "description": "Lentilles corail 500 g",
        "quantity": 6,
        "achat_ht": 3.000,
        "achat_tva": 3.30
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760346021141",
        "description": "Pois cassés 500 g",
        "quantity": 6,
        "achat_ht": 3.000,
        "achat_tva": 2.20
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760346021134",
        "description": "Pois chiches 500 g",
        "quantity": 6,
        "achat_ht": 3.000,
        "achat_tva": 1.90
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3268350120534",
        "description": "P’tit Déj’ chocolat miel 190 g",
        "quantity": 12,
        "achat_ht": 2.280,
        "achat_tva": 2.98
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "376009533595",
        "description": "Gaufres nature pur beurre",
        "quantity": 12,
        "achat_ht": 2.040,
        "achat_tva": 3.04
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3375190031026",
        "description": "Huîles d'olive vierge extra 1L",
        "quantity": 6,
        "achat_ht": 5.478,
        "achat_tva": 13.07
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760074475575",
        "description": "Nectar de pèche 75 cl",
        "quantity": 6,
        "achat_ht": 4.500,
        "achat_tva": 2.55
    },
    {
        "provider": "Allée Jean Marie AHELIN",
        "ean": "3760074474820",
        "description": "Jus de pomme 1 L",
        "quantity": 6,
        "achat_ht": 6.000,
        "achat_tva": 2.64
    }
]
'''  
        json_data = json.loads(str)
        inventory = Inventory.get('testInventory')
        error_list = json_to_db(json_data, inventory)
        self.assertTrue(error_list)
    



