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

class Mistral_API():

    mistral_api_key = config("MISTRAL_API_KEY", default="", cast=str)
    model = "pixtral-12b-2409"
    client = Mistral(api_key=mistral_api_key)


    def chat(self, message, products):
        chat_response = self.client.chat.complete(
            model= self.model,
            messages = [
                {
                    "role": "system",
                    "content": '''
                                Le message de l'utilisateur sera toujours fini par un dataset.
                                Il y a de grandes chances que la réponse a la question se trouve dedans.
                                Dans ta réponse, n'en fait pas trop, contente toi de répondre simplement a la question.
                                Si tu ne connais pas la réponse a la question, dit le et n'imvente pas de résultat.
                                ''',
                },
                {
                    "role": "user",
                    "content": f'{message} - {products}',
                },
              
            ]
        )
        return chat_response.choices[0].message.content

    def upload(self, filepath):
        return self.client.upload(
            file={
                "file_name": filepath,
                "content": open(filepath, "rb"),
            }
        )
    
    def extract_json_from_image(self, formatted_images):
        content = [{
                    "type": "text",
                    "text": '''
                        Voici le bon de livraison. Extrait les éléments et retourne les données dans un fichier JSON formatées comme ci-dessous :
                        
                        {
                            fournisseur : {
                                name: value,
                                n_tva: value 
                            },
                            produits : [
                                {
                                    ean : value,
                                    description : value,
                                    quantity : value,
                                    achat_brut : value
                                },
                                {
                                    ean : value,
                                    description : value,
                                    quantity : value,
                                    achat_brut : value
                                }
                            ]
                        }
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
                                    Le but est de créer un fichier JSON, avec pour le fournisseur :
                                        - name
                                        - n_tva 
                                    Et pour chaque produits : 
                                        - ean
                                        - description
                                        - quantity
                                        - achat_brut


                                    Pour ce faire, tu vas réaliser plusieurs étapes.

                                    ETAPE 1 - Identifier les données fournisseur suivants :
                                        - name - C'est le nom du fournisseur
                                        - n_tva - C'est le numéro TVA Intracommunautaire. Souvent N° TVA Intra.

                                    ETAPE 2 - Identifier les colonnes du tableau qui correspondent aux élements du fichier JSON :
                                        - ean - le code EAN du produit. Il consiste en une suite de 13 chiffres.
                                        - description - le nom ou la description du produit
                                        - quantity - La colonne 'Qté', 'PCB', 'Pièces' ou 'Quantité'
                                        - achat_brut - La colonne 'PU HT' ou 'PU H.T.'  

                                    ETAPE 3 - Construire le JSON
                                        - Le fichier correspond a un objet JSON, contenant le fournisseur et les produits.
                                        - Le JSON est un objet, pas une liste.
                                    
                                    ETAPE 4 - Renvoyer le JSON
                                        - Ta réponse ne doit comporter UNIQUEMENT le JSON et rien d'autre. Ne soit pas verbeux.
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

   
