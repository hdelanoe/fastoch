from paddlex import create_pipeline
from django.conf import settings


def table_recognition(img_path):

    pipeline = create_pipeline(pipeline="table_recognition")

    output = pipeline.predict(img_path)
    for res in output:
    #res.print()  # Print the structured output of the prediction
    #res.save_to_img("./output/")  # Save the results in img format
        res.save_to_xlsx(f'{settings.MEDIA_ROOT}')  # Save the results in Excel format
        #res.save_to_html(f'{settings.MEDIA_ROOT}') # Save results in HTML format
