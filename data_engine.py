import pandas as pd
import numpy as np

def convertWithoutStem(cell):
    return cell
    pass
def get_origin_data(data_sent_path,data_answer_path):
    obj_data_origin_sentence = pd.read_csv(data_sent_path,converters={
    'sent0':convertWithoutStem,
    'sent1':convertWithoutStem
    })
    result  = pd.DataFrame()
    obj_data_origin_label = pd.read_csv(data_answer_path,header=None)
    obj_data_origin_label.columns = ['0','1']
    sents = []
    labels = []
    index = 0
    for sent0 in obj_data_origin_sentence['sent0']:
        sents.append(sent0)
        sents.append(obj_data_origin_sentence['sent1'][index])
        label = 0
        if(obj_data_origin_label['1'][index] == 0):
            label = 1
            labels.append(label)
            labels.append(0)
            pass
        else:
            label = 0
            labels.append(label)
            labels.append(1)
        index+=1
        pass
    result['sent'] = sents
    result['label'] = labels
    # print(result.head(10))
    return result
    pass