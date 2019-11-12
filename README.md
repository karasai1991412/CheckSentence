
## Training


usage: main.py    [--mode 'train']
                  [--ModelPath 'Model']
                  [--linesToTrain 20000]
                  [--data_sent_path './data_all.csv']
                  [--data_answer_path './taskA_answers_all.csv']
                  [--epochs 3]
                  
## Estimating



usage: main.py    [--mode 'estimate']
                  [--data_sent_path './data_all.csv']
                  [--data_output './']
                  [--n_lines 200]
                  

## predicting



usage: main.py    [--mode 'predict']
                  [--sentence 'He drinks milk']
                  

## get Accracy


usage: main.py    [--mode 'getAcc']


## get 10 cross validation


usage: main.py    [--mode 'crossValidation']
                  [--ModelPath 'Model']
                  [--data_sent_path './data_all.csv']
                  [--data_answer_path './taskA_answers_all.csv']


## git install


    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
    sudo apt-get install git-lfs
    git lfs install

    git clone https://github.com/karasai1991412/CheckSentence
    
    git lfs fetch --all
	