import pandas as pd
import numpy as np
import estimator
import argparse
import train
import estimator
import os.path
from os import path
class Engine:
    def __init__(self,args):
        self.args = args
        pass
    def run(self):
        if(self.args.mode == 'train'):
            #train model for sentences and labels based on data_sent_path and data_answer_path
            if(path.exists(self.args.data_sent_path) and path.exists(self.args.data_answer_path)):
                pass
            else:
                print("pls insert data_sent_path and data_answer_path")
                return
                pass
            train.run(OUTPUT_DIR = self.args.ModelPath,data_sent_path = self.args.data_sent_path,data_answer_path=self.args.data_answer_path,NUM_TRAIN_EPOCHS = self.args.epochs,n_train=self.args.linesToTrain)

            pass
        elif(self.args.mode == 'estimate'):
            #make result_answers_all.csv file and compare it to original
            estimator.config(self.args.ModelPath)
            estimator.run(self.args.data_sent_path,n_lines=self.args.n_lines,outputpath=self.args.data_output)
            pass
        elif(self.args.mode == 'getAcc'):
            #make result_answers_all.csv file and compare it to original
            print(self.get_acc())
            pass
        else:
            #predict the sentence
            estimator.config(self.args.ModelPath)
            sents = [""]
            sents.append(self.args.sentence)
            predictions = estimator.getPrediction(sents)
            print(predictions[1][2])
            return predictions[1][2]
            pass
        pass
    def get_acc(self):
        origin = pd.read_csv(self.args.data_answer_path,header=None)
        origin.columns = ['0','1']
        result = pd.read_csv(self.args.data_output+"result_answers_all.csv")
        n_all = result.shape[0]
        n_correct = 0
        index = 0
        for item in result['labels'].values:
            if(item == origin['1'][index]):
                n_correct+=1
            else:
                pass
            pass
            index+=1
        print(str(100*n_correct/n_all)+" %")
        return(n_correct,n_all)
        pass

if __name__ == '__main__':
    import warnings

    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser()

    """
    Data Argument
    """
    parser.add_argument('--ModelPath', type=str, default="Model")
    parser.add_argument('--mode', type=str, default='getAcc')
    parser.add_argument('--sentence', type=str, default="He drinks milk")
    parser.add_argument('--linesToTrain', type=int, default=20000)
    parser.add_argument('--n_lines', type=int, default=200)

    # Path Argument
    parser.add_argument('--data_sent_path', type=str, default='./data_all.csv',
                        help='the path for input sentence')
    parser.add_argument('--data_answer_path', type=str, default='./taskA_answers_all.csv',
                        help='the path for answers for the group of sentence')
    parser.add_argument('--data_output', type=str, default='./',
                        help='path for output')
    """
    Training Argument
    """
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--learning_rate', type=int, default=0.001)
    parser.add_argument('--epochs', type=int, default=3)

    args = parser.parse_args()
    engine = Engine(args)
    engine.run()