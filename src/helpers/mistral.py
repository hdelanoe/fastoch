import base64
import json
from decouple import config
from mistralai import Mistral
import logging

logger = logging.getLogger('fastoch')

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

class Mistral_Nemo_API():

    mistral_api_key = config("MISTRAL_API_KEY", default="", cast=str)
    model = "open-mistral-nemo"
    client = Mistral(api_key=mistral_api_key)

    def extract_json_from_html(self, table):
        prebuild = {
                    "type": "text",
                    "text": '''
                        Voici un tableau mal formaté issu de l'OCR d'une image.
                        Il décrit un bon de livraison et les informations de chaque produit.
                        Veuillez trier les données et les ranger dans un fichier JSON.
                        -----

                    '''
                }
        prebuild["text"] += table
        content = [prebuild]
        chat_response = self.client.chat.complete(
            model = self.model,
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text" : '''
                                L'utilisateur va fournir un tableau mal formaté sous la forme d'un csv.
                                Ton rôle est d'analyser le tableau, de trier correctement les données de chaque produit.
                                Ensuite il faut créer une liste JSON détaillant certaines colonnes pour chaque produit du tableau.


                                 1. Format de sortie JSON :
                                    Le résultat doit être une liste JSON. Chaque produit doit être représenté par un objet structuré de la manière suivante :

                                        [
                                        {
                                            "code_art": "<valeur>",
                                            "ean": "<valeur>",
                                            "description": "<valeur>",
                                            "quantity": <valeur>,
                                            "achat_ht": <valeur>
                                        },
                                        ...
                                        ]


                                2. Correspondance des colonnes :
                                    'code_art' : correspond aux colonnes intitulées 'Code art.', 'Réf.' ou 'REF'.
                                        Une suite de lettres et/ou chiffres. Il n'est pas toujours présent.
                                    'ean' : correspond aux colonnes intitulées 'ean' ou 'EAN'.
                                        C'est le seul entier de 13 chiffres de la ligne. Il n'est pas toujours présent.
                                    'description' : correspond par ordre de priorité aux colonnes intitulées 'Produit', 'Désignation' ou 'Description'.
                                        Une phrase décrivant le produit.
                                    'quantity' : correspond, par ordre de priorité, aux colonnes intitulées 'Qté totale', 'Qté', 'PCB', 'Pièces' ou 'Quantité'.
                                        Un nombre entier
                                    'achat_ht' : correspond aux colonnes intitulées 'PU HT', 'Prix U. HT' ou 'PU H.T.'. Ignorez la colonne 'Total HT'.
                                        Un nombre flottant.


                                Le format doit contenir uniquement la liste JSON, sans texte supplémentaire ni explications.
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
        logger.debug('extract_json_from_html')
        logger.debug(chat_response.choices[0].message.content)
        return json.loads(chat_response.choices[0].message.content, strict=False)

class Mistral_PDF_API():

    mistral_api_key = config("MISTRAL_API_KEY", default="", cast=str)
    model = "pixtral-large-2411"
    client = Mistral(api_key=mistral_api_key)



    def extract_json_from_image(self, formatted_images):
        content = [{
                    "type": "text",
                    "text": '''
                        This is a sample delivery note.
                        Please extract numeric data accurately, it's very important.

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
                                Extraire les données des images des bons de livraison en respectant les consignes suivantes :

                                    1. Correspondance des colonnes :
                                        'code_art' : correspond aux colonnes intitulées 'Code art.', 'Réf.' ou 'REF'.
                                        'ean' : correspond aux colonnes intitulées 'ean' ou 'EAN'.
                                        'description' : correspond au nom ou à la description du produit.
                                        'quantity' : correspond, par ordre de priorité, aux colonnes intitulées 'Qté totale', 'Qté', 'PCB', 'Pièces' ou 'Quantité'.
                                        'achat_ht' : correspond aux colonnes intitulées 'PU HT', 'Prix U. HT' ou 'PU H.T.'.

                                    2. Précision des valeurs numériques :
                                    Toutes les valeurs numériques doivent être extraites avec une précision absolue, sans erreurs.

                                    3. Fusion des colonnes pour un même produit :
                                    Si plusieurs colonnes contiennent des informations liées au même produit, fusionnez les valeurs correspondantes pour créer un objet unique.

                                    4. Colonnes ignorées :
                                    Ignorez complètement les colonnes non pertinentes telles que 'Poids' ou 'Colis'.

                                    5. Format de sortie JSON :
                                    Le résultat doit être une liste JSON. Chaque produit doit être représenté par un objet structuré de la manière suivante :

                                        [
                                        {
                                            "code_art": "<valeur>",
                                            "ean": "<valeur>",
                                            "description": "<valeur>",
                                            "quantity": <valeur>,
                                            "achat_ht": <valeur>
                                        },
                                        ...
                                        ]

                                    Si une donnée est absente pour un produit, excluez la clé correspondante de l’objet.
                                    Le format doit contenir uniquement la liste JSON, sans texte supplémentaire ni explications.
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
        logger.debug('extract_json_from_image')
        logger.debug(chat_response.choices[0].message.content)
        return json.loads(chat_response.choices[0].message.content, strict=False)

    def replace_ean_by_tesseract(self, old_json, text):
        prebuild_content = {
                    "type": "text",
                    "text": '''
                        First it's the JSON, second the text.
                        Please replace all the JSON "ean" values by those in the text.
                        ----

                    '''
                }
        prebuild_content["text"] += str(old_json)
        prebuild_content["text"] += '''
                                    -----
                                    '''
        prebuild_content["text"] += str(text)
        content = [prebuild_content]
        chat_response = self.client.chat.complete(
            model = self.model,
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text" : '''
                                    "I will provide a JSON file and a text. The JSON is a list of elements who contains a key called EAN with associated values.
                                    EAN are a string of 13 numbers.
                                    Analyze the text to find matches with the JSON elements and replace only the EAN values with those extracted from the text when they match.
                                    Replace Only the EAN. Other values MUST stay unchanged.
                                    Return the modified JSON with the same format :

                                    [
                                        {
                                            "code_art": "<unchanged value>",
                                            "ean": "<replaced value>",
                                            "description": "<unchanged value>",
                                            "quantity": <unchanged value>,
                                            "achat_ht": <unchanged value>
                                        },
                                        ...
                                    ]

                                    Return only the JSON, nothing else.
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
        logger.debug('replace_ean_by_tesseract')
        logger.debug(chat_response.choices[0].message.content)
        return json.loads(chat_response.choices[0].message.content, strict=False)

def format_content_from_image_path(image_path):
    try:
        with open(image_path, "rb") as image_file:
             base64_image =  base64.b64encode(image_file.read()).decode('utf-8')
             return {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{base64_image}",
            }
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:  # Added general exception handling
        print(f"Error: {e}")
        return None
