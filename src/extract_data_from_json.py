import tqdm
import pandas as pd
import os
import argparse


pos_to_keep = ['adj', 'adv', 'conj', 'det', 'noun', 'prep', 'pron', 'verb']


def dropDuplicates(df):
    return df.loc[df.astype(str).drop_duplicates().index]


def saveAllPos(df, saving_path):
    for pos in tqdm.tqdm(pos_to_keep, desc='Saving Files'):
        file_save_path = os.path.join(saving_path, pos + '.csv')
        words = df[df.pos == pos]
        words = words[['form', 'tags']]
        words = dropDuplicates(words)
        words = words.sort_values(by=['form'])
        words.to_csv(file_save_path, index=False)


def saveDictionary(df, saving_path):
    dictionary_saving_path =\
        os.path.join(saving_path, 'dictionary.csv')

    all_words = df.form
    all_words = dropDuplicates(all_words)
    all_words = all_words.sort_values()
    all_words.to_csv(dictionary_saving_path, index=False, header=False)
    saveAllPos(df, saving_path)


def retrieveMissingWordForms(df):
    pos = df.pos.to_list()
    forms = df.form.to_list()
    words = df.word.to_list()
    pos_forms = set(list(zip(pos, forms)))
    pos_words = set(list(zip(pos, words)))

    missing_word_forms = list(pos_words - pos_forms)

    d = {}
    for i in tqdm.tqdm(range(len(missing_word_forms)),
                       desc='Retrieving Missing Words'):

        d[i] = {"pos": missing_word_forms[i][0],
                "form": missing_word_forms[i][1],
                "tags": None,
                "word": missing_word_forms[i][1]}

    df_2 = pd.DataFrame.from_dict(d, 'index')

    return pd.concat([df, df_2])


def extractData(json_file_path, saving_path):
    data = pd.read_json(json_file_path, lines=True)
    data = data[['pos', 'forms', 'word']]
    data = data[data.pos.isin(pos_to_keep)]
    data = data.where(pd.notnull(data), None)
    data = dropDuplicates(data)
    data = data.reset_index(drop=True)

    d = {}
    j = 0

    for i in tqdm.tqdm(range(len(data)), desc='Extracting Data'):
        pos = data.pos[i]
        forms = data.forms[i]
        word = data.word[i]

        if forms is not None:
            forms = pd.json_normalize(forms)
            forms = forms[['form', 'tags']]
            forms = forms.replace('', None)
            forms = forms[forms['form'].str.contains('\+') == False]
            forms = forms.reset_index(drop=True)
            form = forms.form.to_list()
            tags = forms.tags.to_list()

            for k in range(len(form)):
                d[j] = {"pos": pos, "form": form[k],
                        "tags": tags[k], "word": word}
                j += 1
        else:
            d[j] = {"pos": pos, "form": word, "tags": None, "word": word}
            j += 1

    df = pd.DataFrame.from_dict(d, 'index')
    df = retrieveMissingWordForms(df)
    df = dropDuplicates(df)
    df = df.reset_index(drop=True)
    saveDictionary(df=df, saving_path=saving_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description='Extract Data From Wiktionary JSON'
             )

    parser.add_argument(
        '--json_file_path',
        '-i',
        type=str,
        help='Path to the wiktionary json file',
        required=True
    )

    parser.add_argument(
        '--saving_path',
        '-s',
        type=str,
        help='Path to the folder that will contain the output csv files',
        required=True
    )

    args = parser.parse_args()
    params = {}
    params['json_file_path'] = args.json_file_path
    params['saving_path'] = args.saving_path

    assert os.path.exists(params['json_file_path']),\
           'Input JSON file not found :('

    if not os.path.exists(params['saving_path']):
        os.makedirs(params['saving_path'])

    extractData(**params)
