import base64
import json
from decouple import config
from mistralai import Mistral

class Mistral_API():

    mistral_api_key = config("MISTRAL_API_KEY", default="", cast=str)
    model = "pixtral-12b-2409"
    client = Mistral(api_key=mistral_api_key)


    def chat(self, message):
        chat_response = self.client.chat.complete(
            model= self.model,
            messages = [
                {
                    "role": "user",
                    "content": f'{message}',
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
                        Voici un bon de livraison. Il contient un tableau qui décrit tout les produits livrés.
                        Je veux que tu extrais les données et que tu construises une liste de produits, avec les données ci-dessous :
                    
                        fournisseur - le nom du fournisseur
                        ean - le code EAN du produit, le cas échéant. Il consiste en une suite de 13 chiffres sans espaces.
                        description - le nom ou la description du produit
                        quantity - la quantité totale du produit
                        achat_brut - Le prix unitaire HT
                        achat_tva - la TVA du produit en %. Souvent égale ou aux alentours de 20%. Si cette colonne n'existe pas, cherche a extraire la TVA TOTALE de la livraison.
                        achat_net -  Le prix unitaire TTC a calculer. La formule est : achat_brut + (achat_brut x TVA)

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
                                    Extrait les éléments du bon de livraison décrits par l'utilisateur.
                                    Retourne les données formatées en une liste json, en un liste de produits comme ceci : 
                                    [
                                    {
                                        fournisseur : value,
                                        ean : value,
                                        description : value,
                                        quantity : value,
                                        achat_brut : value,
                                        achat_tva : value,
                                        achat_net : value
                                    },
                                    {
                                        fournisseur : value,
                                        ean : value,
                                        description : value,
                                        quantity : value,
                                        achat_brut : value,
                                        achat_tva : value,
                                        achat_net : value
                                    },
                                    etc...
                                    ]
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
        return json.loads(chat_response.choices[0].message.content)

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

   
