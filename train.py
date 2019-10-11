import data_engine
# from sklearn.model_selection import train_test_split
import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub
from datetime import datetime
import bert
from bert import run_classifier
from bert import optimization
from bert import tokenization
import numpy as np
# Set the output directory for saving model file
# Optionally, set a GCP bucket location

DATA_COLUMN = 'sent'
LABEL_COLUMN = 'label'
label_list = [0, 1]
MAX_SEQ_LENGTH = 128

# This is a path to an uncased (all lowercase) version of BERT
BERT_MODEL_HUB = "https://tfhub.dev/google/bert_uncased_L-12_H-768_A-12/1"
# BERT_MODEL_HUB = "bertModel/uncased_L-12_H-768_A-12"

def create_tokenizer_from_hub_module():
  """Get the vocab file and casing info from the Hub module."""
  with tf.Graph().as_default():
    bert_module = hub.Module(BERT_MODEL_HUB)
    tokenization_info = bert_module(signature="tokenization_info", as_dict=True)
    with tf.Session() as sess:
      vocab_file, do_lower_case = sess.run([tokenization_info["vocab_file"],
                                            tokenization_info["do_lower_case"]])
      
  return bert.tokenization.FullTokenizer(
      vocab_file=vocab_file, do_lower_case=do_lower_case)

tokenizer = create_tokenizer_from_hub_module()
#print(tokenizer.tokenize("This here's an example of using the BERT tokenizer"))

def run(OUTPUT_DIR = 'Model',data_sent_path = './data_all.csv',data_answer_path='./taskA_answers_all.csv',NUM_TRAIN_EPOCHS = 3.0,n_train=20000,train_data=None,test_data=None):

  tf.gfile.MakeDirs(OUTPUT_DIR)
  
  if(train_data == None or test_data == None):
        return None
  # Use the InputExample class from BERT's run_classifier code to create examples from the data
  test_InputExamples = test_data.apply(lambda x: bert.run_classifier.InputExample(guid=None, # Globally unique ID for bookkeeping, unused in this example
                                                                    text_a = x[DATA_COLUMN], 
                                                                    text_b = None, 
                                                                    label = x[LABEL_COLUMN]), axis = 1)

  train_InputExamples = train_data.apply(lambda y: bert.run_classifier.InputExample(guid=None,
                                                                    text_a = y[DATA_COLUMN],
                                                                    text_b = None,
                                                                    label = y[LABEL_COLUMN]), axis = 1)

  # We'll set sequences to be at most 128 tokens long.
  # Convert our train and test features to InputFeatures that BERT understands.
  train_features = bert.run_classifier.convert_examples_to_features(train_InputExamples, label_list, MAX_SEQ_LENGTH, tokenizer)
  test_features = bert.run_classifier.convert_examples_to_features(test_InputExamples, label_list, MAX_SEQ_LENGTH, tokenizer)

  def create_model(is_predicting, input_ids, input_mask, segment_ids, labels,
                  num_labels):
    """Creates a classification model."""

    bert_module = hub.Module(
        BERT_MODEL_HUB,
        trainable=True)
    bert_inputs = dict(
        input_ids=input_ids,
        input_mask=input_mask,
        segment_ids=segment_ids)
    bert_outputs = bert_module(
        inputs=bert_inputs,
        signature="tokens",
        as_dict=True)

    # Use "pooled_output" for classification tasks on an entire sentence.
    # Use "sequence_outputs" for token-level output.
    output_layer = bert_outputs["pooled_output"]

    hidden_size = output_layer.shape[-1].value

    # Create our own layer to tune for politeness data.
    output_weights = tf.get_variable(
        "output_weights", [num_labels, hidden_size],
        initializer=tf.truncated_normal_initializer(stddev=0.02))

    output_bias = tf.get_variable(
        "output_bias", [num_labels], initializer=tf.zeros_initializer())

    with tf.variable_scope("loss"):

      # Dropout helps prevent overfitting
      output_layer = tf.nn.dropout(output_layer, keep_prob=0.9)

      logits = tf.matmul(output_layer, output_weights, transpose_b=True)
      logits = tf.nn.bias_add(logits, output_bias)
      log_probs = tf.nn.log_softmax(logits, axis=-1)

      # Convert labels into one-hot encoding
      one_hot_labels = tf.one_hot(labels, depth=num_labels, dtype=tf.float32)

      predicted_labels = tf.squeeze(tf.argmax(log_probs, axis=-1, output_type=tf.int32))
      # If we're predicting, we want predicted labels and the probabiltiies.
      if is_predicting:
        return (predicted_labels, log_probs)

      # If we're train/eval, compute loss between predicted and actual label
      per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
      loss = tf.reduce_mean(per_example_loss)
      return (loss, predicted_labels, log_probs)
  # model_fn_builder actually creates our model function
  # using the passed parameters for num_labels, learning_rate, etc.
  def model_fn_builder(num_labels, learning_rate, num_train_steps,
                      num_warmup_steps):
    """Returns `model_fn` closure for TPUEstimator."""
    def model_fn(features, labels, mode, params):  # pylint: disable=unused-argument
      """The `model_fn` for TPUEstimator."""

      input_ids = features["input_ids"]
      input_mask = features["input_mask"]
      segment_ids = features["segment_ids"]
      label_ids = features["label_ids"]

      is_predicting = (mode == tf.estimator.ModeKeys.PREDICT)
      
      # TRAIN and EVAL
      if not is_predicting:

        (loss, predicted_labels, log_probs) = create_model(
          is_predicting, input_ids, input_mask, segment_ids, label_ids, num_labels)

        train_op = bert.optimization.create_optimizer(
            loss, learning_rate, num_train_steps, num_warmup_steps, use_tpu=False)

        # Calculate evaluation metrics. 
        def metric_fn(label_ids, predicted_labels):
          accuracy = tf.metrics.accuracy(label_ids, predicted_labels)
          f1_score = tf.contrib.metrics.f1_score(
              label_ids,
              predicted_labels)
          auc = tf.metrics.auc(
              label_ids,
              predicted_labels)
          recall = tf.metrics.recall(
              label_ids,
              predicted_labels)
          precision = tf.metrics.precision(
              label_ids,
              predicted_labels) 
          true_pos = tf.metrics.true_positives(
              label_ids,
              predicted_labels)
          true_neg = tf.metrics.true_negatives(
              label_ids,
              predicted_labels)   
          false_pos = tf.metrics.false_positives(
              label_ids,
              predicted_labels)  
          false_neg = tf.metrics.false_negatives(
              label_ids,
              predicted_labels)
          return {
              "eval_accuracy": accuracy,
              "f1_score": f1_score,
              "auc": auc,
              "precision": precision,
              "recall": recall,
              "true_positives": true_pos,
              "true_negatives": true_neg,
              "false_positives": false_pos,
              "false_negatives": false_neg
          }

        eval_metrics = metric_fn(label_ids, predicted_labels)

        if mode == tf.estimator.ModeKeys.TRAIN:
          return tf.estimator.EstimatorSpec(mode=mode,
            loss=loss,
            train_op=train_op)
        else:
            return tf.estimator.EstimatorSpec(mode=mode,
              loss=loss,
              eval_metric_ops=eval_metrics)
      else:
        (predicted_labels, log_probs) = create_model(
          is_predicting, input_ids, input_mask, segment_ids, label_ids, num_labels)

        predictions = {
            'probabilities': log_probs,
            'labels': predicted_labels
        }
        return tf.estimator.EstimatorSpec(mode, predictions=predictions)

    # Return the actual model function in the closure
    return model_fn


  # Compute train and warmup steps from batch size
  # These hyperparameters are copied from this colab notebook (https://colab.sandbox.google.com/github/tensorflow/tpu/blob/master/tools/colab/bert_finetuning_with_cloud_tpus.ipynb)
  BATCH_SIZE = 32
  LEARNING_RATE = 2e-5
  NUM_TRAIN_EPOCHS = 3.0
  # Warmup is a period of time where hte learning rate 
  # is small and gradually increases--usually helps training.
  WARMUP_PROPORTION = 0.1
  # Model configs
  SAVE_CHECKPOINTS_STEPS = 500
  SAVE_SUMMARY_STEPS = 100
  # Compute # train and warmup steps from batch size
  num_train_steps = int(len(train_features) / BATCH_SIZE * NUM_TRAIN_EPOCHS)
  num_warmup_steps = int(num_train_steps * WARMUP_PROPORTION)


  # Specify outpit directory and number of checkpoint steps to save
  run_config = tf.estimator.RunConfig(
      model_dir=OUTPUT_DIR,
      save_summary_steps=SAVE_SUMMARY_STEPS,
      save_checkpoints_steps=SAVE_CHECKPOINTS_STEPS)

  model_fn = model_fn_builder(
    num_labels=len(label_list),
    learning_rate=LEARNING_RATE,
    num_train_steps=num_train_steps,
    num_warmup_steps=num_warmup_steps)

  estimator = tf.estimator.Estimator(
    model_fn=model_fn,
    config=run_config,
    params={"batch_size": BATCH_SIZE})

  train_input_fn = bert.run_classifier.input_fn_builder(
      features=train_features,
      seq_length=MAX_SEQ_LENGTH,
      is_training=True,
      drop_remainder=False)

  #print(f'Beginning Training!')
  current_time = datetime.now()
  estimator.train(input_fn=train_input_fn, max_steps=num_train_steps)
  #print("Training took time ", datetime.now() - current_time)

  test_input_fn = run_classifier.input_fn_builder(
      features=test_features,
      seq_length=MAX_SEQ_LENGTH,
      is_training=False,
      drop_remainder=False)

  estimator.evaluate(input_fn=test_input_fn, steps=None)
  return estimator

from sklearn.model_selection import KFold
import estimator
def k_fold_cross_validation(k = 100,data_sent_path = './data_all.csv',data_answer_path='./taskA_answers_all.csv',ModelPath = "Model"):
      # Applying k-Fold Cross Validation
      data = data_engine.get_origin_data(data_sent_path,data_answer_path)
      kf = KFold(n_splits=k)
      n_list_acc = []
      for train,test in kf.split(data['sent']):
            train_data = data.iloc[train]
            test_data = data.iloc[test]
            # estimator =  run(train_data=train_data,test_data=test_data)
            estimator_local = estimator.config(ModelPath)
            result = getPrediction(in_sentences=test_data['sent'],estimator=estimator_local)
            labels = [1 if item[2] == 'Sensitive' else 0 for item in result]
            n_filter = test_data['label'] == labels
            acc = int(test_data[n_filter].shape[0]*100/test_data.shape[0])
            print(acc)
            n_list_acc.append(acc)
            pass
      print(np.mean(n_list_acc),n_list_acc)
      return np.mean(n_list_acc),n_list_acc
      pass
def get_train_test_data(k = 10,data_sent_path = './data_all.csv',data_answer_path='./taskA_answers_all.csv'):
      data = data_engine.get_origin_data(data_sent_path,data_answer_path)
      test_size = int(len(data)/10)
      train_size = len(data) - test_size
      train = data.iloc[:train_size]
      test = data.iloc[train_size:]
      return (train,test)
      pass
def getPrediction(in_sentences,estimator = None):
    if(estimator == None):
          return None
    labels = ["Non-Sensitive", "Sensitive"]
    input_examples = [run_classifier.InputExample(guid="", text_a = x, text_b = None, label = 0) for x in in_sentences]
    input_features = run_classifier.convert_examples_to_features(input_examples, label_list, MAX_SEQ_LENGTH, tokenizer)
    predict_input_fn = run_classifier.input_fn_builder(features=input_features, seq_length=MAX_SEQ_LENGTH, is_training=False, drop_remainder=False)
    predictions = estimator.predict(predict_input_fn)
    return [(sentence, prediction['probabilities'], labels[prediction['labels']]) for sentence, prediction in zip(in_sentences, predictions)]



