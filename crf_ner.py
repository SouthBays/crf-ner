# -*- coding: utf-8 -*-
# author shakeryoung
# create 2021-01-14
# CRF:安装:pip install crfpy
# crf_learn  -f 3 -c 4.0 template NER_train.data NER.model -t -m 200
# crf_test -m NER.model NER_test.data > result.txt
import CRFPP
import subprocess

root = None


def split_corpus(corpus_dir, ratio=0.9, train_dir='train.data', test_dir='test.data'):
    with open("%s/%s" % (root, corpus_dir), "r", encoding='utf-8') as f:
        sents = [line.strip() for line in f.readlines()]

    # 训练集与测试集的比例为9:1
    train_num = int((len(sents) // 3) * ratio)

    # 将文件分为训练集与测试集
    with open("%s/%s" % (root, train_dir), "w", encoding='utf-8') as g:
        for i in range(train_num):
            words = sents[3 * i].split('\t')
            postags = sents[3 * i + 1].split('\t')
            tags = sents[3 * i + 2].split('\t')
            for word, postag, tag in zip(words, postags, tags):
                g.write(word + ' ' + postag + ' ' + tag + '\n')
            g.write('\n')
        print('train', train_num)

    with open("%s/%s" % (root, test_dir), "w", encoding='utf-8') as h:
        for i in range(train_num + 1, len(sents) // 3):
            words = sents[3 * i].split('\t')
            postags = sents[3 * i + 1].split('\t')
            tags = sents[3 * i + 2].split('\t')
            for word, postag, tag in zip(words, postags, tags):
                h.write(word + ' ' + postag + ' ' + tag + '\n')
            h.write('\n')
        print('test', len(sents) // 3 - train_num)
    print('OK!')


def train_and_test_corpus(train_dir, model, test_dir):
    cmd = 'crf_learn -f 3 -c 5.0 %s/template %s/%s %s/%s -t' % (root, root, train_dir, root, model)
    print('-' * 10, 'training cmd', '-' * 10)
    print(cmd)
    print('-' * 10, 'training cmd', '-' * 10)
    process_cmd(1, *cmd.split(' '))
    print('train data:')
    get_test_acc(test_dir=train_dir, model=model)
    print('test data')
    get_test_acc(test_dir=test_dir, model=model)


def get_test_acc(test_dir, model):
    crf = CRF(model_path=model)
    records = []
    record = [[], [], []]
    with open("%s/%s" % (root, test_dir), "r", encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                records.append(record)
                record = [[], [], []]
            else:
                chs = line.split(' ')
                record[0].append(chs[0])
                record[1].append(chs[1])
                record[2].append(chs[2])
    print(len(records))

    c1 = 0
    c2 = 0
    import time
    t = time.time()
    for record in records:
        orignal_tags = record[2]
        predict_tags, per = crf.ner(record[0], record[1])
        for t1, t2 in zip(orignal_tags, predict_tags):
            c1 += 1
            if t1 == t2:
                c2 += 1
    print((time.time() - t) / len(records))
    print('acc:%5f' % (c2 / c1))


def process_cmd(is_print, *args):
    if not is_print:
        popen = subprocess.Popen(args)
        popen.wait()
        print('OK!')
    else:
        popen = subprocess.Popen(args, stdout=subprocess.PIPE)
        count = 0
        for i in range(1000):
            line = popen.stdout.readline()
            line_callback(line)
            if 'Done!' in line.decode('utf-8'):
                count += 1
                if count == 2:
                    break


# 回调方法，用于处理每行输出的字符串
def line_callback(line_str):
    print(line_str.decode('utf-8'), end='')


class CRF:
    def __init__(self, model_path):
        self.tagger: CRFPP.Tagger = CRFPP.Tagger("-m %s/%s" % (root, model_path))

    def ner(self, text, pos=None, sep=' '):
        self.tagger.clear()
        for i in range(len(text)):
            word = text[i]
            if pos:
                self.tagger.add("{} {} O".format(word, pos[i]))
            else:
                self.tagger.add("{} n O".format(word))
        self.tagger.parse()
        size = self.tagger.size()

        # 获取模型预测标签
        predict_tags = [self.tagger.y2(i) for i in range(0, size)]
        extracted = []
        entity, buffer = None, []
        for ch, tag in zip(text, predict_tags):
            if tag.startswith('B'):
                if not entity:
                    entity = tag.replace('B-', '')
                    if not buffer:
                        buffer.append(ch)
                    else:
                        extracted.append(sep.join(buffer))
                        buffer = [ch]
                else:
                    entity = tag.replace('B-', '')
                    buffer = [ch]
                    if buffer:
                        extracted.append(sep.join(buffer))
            elif tag.startswith("I"):
                if entity == tag.replace('I-', '') and buffer:
                    buffer.append(ch)
                else:
                    entity, buffer = None, []
            elif tag == 'O':
                if entity and buffer:
                    extracted.append(sep.join(buffer))
                    entity, buffer = None, []
                else:
                    entity, buffer = None, []
        if entity and buffer:
            extracted.append(sep.join(buffer))
        return predict_tags, extracted


def main():
    global root
    root = "data/ABBR"
    if 1:
        split_corpus(corpus_dir='company_shortname_corpus.txt',
                     train_dir='rain.data',
                     test_dir='test.data')
        train_and_test_corpus(train_dir='train.data',
                              model='model',
                              test_dir='test.data')
    crf = CRF(model_path='model')
    for text in """杭州宠伴网络技术有限公司
杭州新橙健康管理有限公司
杭州浙里农享农业科技有限公司
杭州太之迷健康科技有限公司
杭州智哲隆科技有限公司
杭州旗开晟企业管理合伙企业（有限合伙）
杭州越腾供应链有限公司
杭州信哲诚科技有限公司
中智云福（杭州）医疗科技有限公司
杭州盈盈美业科技有限公司
杭州中晟融信科技有限公司
聚合优美（杭州）医疗管理有限公司""".split('\n'):
        print(crf.ner(text, sep=''))


if __name__ == '__main__':
    main()
