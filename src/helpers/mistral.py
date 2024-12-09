import base64
import json
from decouple import config
from mistralai import Mistral

class Codestral_Mamba():
    
    mistral_api_key = config("MISTRAL_API_KEY", default="", cast=str)
    model = "open-mistral-nemo"
    client = Mistral(api_key=mistral_api_key)

    def chat(self, message, products):
        print(products)
        content=[
            {message},
            {str(products)}
        ]
        chat_response = self.client.chat.complete(
            model= self.model,
            messages = [
                {
                    "role": "system",
                    "content": '''
                                Le message de l'utilisateur sera toujours accompagné par un DataFrame pandas.
                                Ce Dataframe correspond a une liste de produits dans un inventaire.
                                N'oublie pas que le DataFrame commence avec l'index 0.
                                Extrais-en les éléments demandées par l'utilisateur puis repond uniquement avec la réponse et quelques détails.
                                
                                ''',
                },
                {
                    "role": "user",
                    "content": f'{content}',
                },
              
            ]
        )
        return chat_response.choices[0].message.content

class Mistral_PDF_API():

    mistral_api_key = config("MISTRAL_API_KEY", default="", cast=str)
    model = "pixtral-12b-2409"
    client = Mistral(api_key=mistral_api_key)


    def extract_json_from_image(self, formatted_images):
        content = [{
                    "type": "text",
                    "text": '''
                        Voici le bon de livraison. Extrait les éléments et retourne les données dans un fichier JSON formatées comme ci-dessous :
                        
                        [
                            {
                                code_art : value,
                                ean : value,
                                description : value,
                                quantity : value,
                                achat_ht : value,
                            },
                            {
                                code_art : value,
                                ean : value,
                                description : value,
                                quantity : value,
                                achat_ht : value,
                            }
                        ]

                        Si aucun élément du tableau ne correspond a une clé, ne l'ajoute pas. Si un produit est en double, compte le deux fois.
                    '''
                }]
        for fi in formatted_images:
            content.append(fi)
        chat_response = self.client.chat.complete(
            model = self.model,
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text" : '''
                                    L'utilisateur fourni une ou des images correspondants a un  bon de livraison. Ce dernier comporte un tableau détaillant chaque produit.
                                    Le but est de créer un fichier JSON, avec pour chaque produits : 
                                        - code_art
                                        - ean
                                        - description
                                        - quantity
                                        - achat_ht


                                    Chaque ligne du tableau correspond a un produit et doit etre traitée comme tel.    
                                    Pour ce faire, tu vas réaliser plusieurs étapes. Les étapes 1 et 2 contextualisent les données que tu dois extraire. 
                                    L'étape 3 est importante car elle explicite les limites et regles que tu dois appliquer. Les étapes 4 et 5 figurent la construction du JSON.

                                    
                                    ETAPE 1 - Identifier les colonnes du tableau qui correspondent aux élements du fichier JSON :
                                        - code_art - un code unique identifiant le produit. Prend bien toute la chaine de caracteres.
                                        - ean - le code EAN du produit. Il consiste en une suite de 13 chiffres.
                                        - description - le nom ou la description du produit
                                        - quantity - La quantité du produit.
                                        - achat_ht - Le prix unitaire hors taxe.

                                    ETAPE 2 - Vérifier l'intégrité des ensembles clé/valeurs :
                                        - 'code_art' ne peut correspondre qu'avec une colonne 'Code art.', 'Réf.' ou 'REF'.
                                        - 'ean' ne peut correspondre qu'avec une colonne 'ean' ou 'EAN'
                                        - 'quantity' ne peut correspondre qu'avec une colonne, dans l'ordre des priorités, 'Qté totale', 'Qté', 'PCB', 'Pièces' ou 'Quantité'.  
                                        - 'achat_ht' ne peut correspondre qu'avec une colonne 'PU HT', 'Prix U. HT' ou 'PU H.T.'     

                                    ETAPE 3 - Prend en compte les précisions suivantes : 
                                        - Il y a autant d'objets dans la liste JSON que de produits dans le tableau a analyser.
                                        - Si la colonne d'une clé n'existe pas dans le tableau, ne l'invente pas et ne l'inclue pas dans le JSON final. Par example, si il n'y a pas de colonne EAN, ne l'ajoute pas.
                                        ne fait pas non plus correspondre le PU HT au poids.
                                        - Si le meme produit est présent plusieurs fois dans le tableau, crée donc autant d'entrée dans le JSON final.
                                        - 'code_art' et 'ean' sont deux identifiants différents.
                                        - 'achat_ht' est le prix unitaire hors taxe, pas le prix total.    

                                    ETAPE 4 - Construire le JSON
                                        - Le fichier correspond a une liste JSON, contenant les produits.
                                        - Le JSON est une liste, pas un objet contenant une liste.
                                    
                                    ETAPE 5 - Renvoyer le JSON
                                        - Ta réponse ne doit comporter UNIQUEMENT la liste JSON et rien d'autre. Ne soit pas verbeux.
                                    '''
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": content,
                }
            ],
            response_format = {"type": "json_object"}
        )
        print(chat_response.choices[0].message.content)
        return json.loads(chat_response.choices[0].message.content, strict=False)

def format_content_from_image_path(image_path):
    try:
        with open(image_path, "rb") as image_file:
             base64_image =  base64.b64encode(image_file.read()).decode('utf-8')
             return {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{base64_image}",
            }
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:  # Added general exception handling
        print(f"Error: {e}")
        return None

   
