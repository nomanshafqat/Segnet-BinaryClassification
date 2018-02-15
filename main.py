from Model2 import SegNet
from dataset import parse, prepare_batch
import tensorflow as tf
from loss import loss
import numpy as np
import sys
import os

batchsize = 2
imgdir = ""
groundtruth_dir = ""
total_steps = 1000000
ckpt_dir = "ckpt/"
ckpt_steps = 5000
load = -1
gpu = 0.5
lr = 1e-04

print("--loadfrom;", sys.argv[1], " --ckptdir;", sys.argv[2], " --gpu", sys.argv[3], " --lr", sys.argv[4], "save",
      sys.argv[5])

# python main.py -1 ckpt 0.5 1e-4 100 2


load = int(sys.argv[1])
ckpt_dir = sys.argv[2]
gpu = float(sys.argv[3])
lr = float(sys.argv[4])
ckpt_steps = int(sys.argv[5])
batchsize = int(sys.argv[6])
imgdir=sys.argv[7]
groundtruth_dir=sys.argv[8]

assert (os.path.exists(ckpt_dir))
assert (os.path.exists(imgdir))
assert (os.path.exists(groundtruth_dir))

# tensor_in=tf.constant(1.0,shape=[batchsize,224,224,1],dtype=tf.float32)
segnet = SegNet(batchsize)

gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu)
session_config = tf.ConfigProto(allow_soft_placement=True, gpu_options=gpu_options)

train_batch = tf.placeholder(dtype=tf.float32, shape=[batchsize, 512, 512, 3])
labels = tf.placeholder(dtype=tf.int32, shape=[batchsize, 512, 512])

print(train_batch.get_shape().as_list())
with tf.variable_scope("One-Hot-Labels"):
    onehot = tf.one_hot(labels, 2)

logits = segnet.inference(train_batch)

print("logits=", logits.get_shape().as_list())
print("labels=", labels.get_shape().as_list())

loss_op = loss(logits, onehot)

optimizer = tf.train.AdamOptimizer(lr)
train_step = optimizer.minimize(loss_op)

init = tf.global_variables_initializer()

writer = tf.summary.FileWriter("summary/")
mergedsummary = tf.summary.merge_all()

saver = tf.train.Saver()

with tf.Session(config=session_config) as sess:
    sess.run(init)
    start = 0
    if load > 0:
        print("Restoring", load, ".ckpt.....")
        saver.restore(sess, os.path.join(ckpt_dir, str(load)))
        start = load

    for i in range(start, total_steps):
        # print(sess.run(batch))

        _batch, _labels = prepare_batch(imgdir, groundtruth_dir, batchsize)

        # print(_batch.shape)

        _, loss = sess.run([train_step, loss_op], feed_dict={train_batch: _batch, labels: _labels})

        if i % 50 == 0:
            s = sess.run(mergedsummary, feed_dict={train_batch: _batch, labels: _labels})
            writer.add_summary(s, i)
            print("writing summary")

        writer.add_graph(sess.graph)

        print("step", i, "Loss=", loss)

        if i % ckpt_steps == 0 and i != start:
            print("saving checkpoint ", str(i), ".ckpt.....")

            save_path = saver.save(sess, os.path.join(ckpt_dir, str(i)))
