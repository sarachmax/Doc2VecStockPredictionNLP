import pandas as pd
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize
from sklearn.preprocessing import MinMaxScaler 
import numpy as np 

def open_csv():
    """
    Read news data from all CSV files and append them together.
    """
    df = pd.DataFrame(columns=['time', 'headline', 'assetCodes',
                               'sentimentNegative', 'sentimentNeutral',
                               'sentimentPositive'])
    file_count = 10
    for i in range(file_count):
        file_name = "data/news/news_data_" + "{:02}".format(i+1) + ".csv"
        print("Open : " + file_name)
        load_df = pd.read_csv(file_name)
        load_df = load_df[['time', 'headline', 'assetCodes',
                            'sentimentNegative', 'sentimentNeutral',
                            'sentimentPositive']]
        df = df.append(load_df)
    return df

def sector_ric():
    """
    Read sector symbol
    """
    df = pd.read_csv("data/tech_sector_ric.csv")
    ric = df["RIC"].tolist()
    return ric

def clean_headline(text_list):
    """
    Pre-processing the data
    1. cut stock quotes
    2. cut special alphabets
    3. change to lower

    input variable : text_list --> list/series/array of string
    input type : list/series/array-like
    return list/series/array-like of cleaning data
    """
    wantToChange = ['\\\\','...','--', '"', "'", '..'] #ลบตัวที่ไม่ต้องการทิ้ง
    memory = []
    text_list_change = []
    for x in text_list:
        word = str(x)
        if ('{' in word):
            wordSplit = word.split('{')
            CreateWord = ''
            for y in range(len(wordSplit)-1):
                if CreateWord == '' and len(CreateWord.split('}')) != 1:
                    CreateWord = CreateWord + wordSplit[0] + wordSplit[1].split('}')[1]
                elif len(CreateWord.split('}')) != 1:
                    CreateWord = CreateWord.split('{')[0]+CreateWord.split('}')[1]
                else:
                    CreateWord = CreateWord.split('{')[0]
        
            word = CreateWord
        if '(' in word:
            wordSplit = word.split('(')
            CreateWord = ''
            for y in range(len(wordSplit)-1):
                if CreateWord == '' and len(CreateWord.split(')')) != 1:
                    CreateWord = CreateWord + wordSplit[0] + wordSplit[1].split(')')[1]
                elif len(CreateWord.split(')')) != 1:
                    CreateWord = CreateWord.split('(')[0]+CreateWord.split(')')[1]
                else:
                    CreateWord = CreateWord.split('(')[0]
        
            word = CreateWord
        if '<' in word:
            wordSplit = word.split('<')
            CreateWord = ''
            # try:
            for y in range(len(wordSplit)-1):
                if CreateWord == '' and len(CreateWord.split('>')) != 1:
                    CreateWord = CreateWord + wordSplit[0] + wordSplit[1].split('>')[1]
                elif len(CreateWord.split('>')) != 1:
                    CreateWord = CreateWord.split('<')[0]+CreateWord.split('>')[1]
                else:
                    CreateWord = CreateWord.split('<')[0]
        
            word = CreateWord

        if '- Part' in word:
            word = word.split('- Part')[0]
        
        for a in range(len(wantToChange)):
            if wantToChange[a] in word:
                word = word.replace(wantToChange[a],'')        

        while '  ' in word:
            word = word.replace('  ',' ')
        
        if ' ' in word:
            if word[0] == ' ':
                word = word[1:]

        word = word.lower()

        text_list_change.append(word)
    return text_list_change

def encode_to_doc2vec(model, text_list, verbose=False):
    """
    Encode document

    input variable : text_list --> list/series/array of string
    input type : list/series/array-like
    return 2d list/array
    """
    doc_vector = []
    for paragraph in text_list :
        vec = model.infer_vector(paragraph)
        doc_vector.append(vec)
        if verbose :
            print("Encode : " + paragraph + " to ", vec)
    return doc_vector

def select_data(df, ric):
    """
    Select only used data
    """
    df = df[df["assetCodes"].str.contains(ric)]
    df = df.dropna()
    return df

def combine_duplicate_headline(df):
    df = df.set_index(df.time)
    df = df.groupby(df.headline, as_index=False).mean()
    return df

def sort_data(df):
    df.time = pd.to_datetime(df.time)
    df = df.sort_values(by='time')
    df = sum_sentiment(df)
    df = df[['time','headline', 'sentiment']]
    return df

def sum_sentiment(df):
    df['sentiment'] = df['sentimentPositive'] - df['sentimentNegative']
    sc = MinMaxScaler(feature_range=(-1,1))
    df['sentiment'] = sc.fit_transform(df[['sentiment']])
    return df     

def match_data_with_timestamp(df_source, df_used):
    df_used = df_used.merge(df_source[['time','headline']].drop_duplicates('headline'))
#    df_used = df_used.dropna(subset=df_used.headline)
    df_used = sort_data(df_used)
    return df_used

def convert_vector_to_dataframe(doc2vec):
    colums_h = np.array(range(1,21))
    doc_col = pd.DataFrame(doc2vec, columns=colums_h)   
    return doc_col 


if __name__ == "__main__":
    model= Doc2Vec.load("weight/d2v_final.model")
    news_df = open_csv()
    goog_df = select_data(news_df, 'GOOG')
    goog_df['headline'] = clean_headline(goog_df.headline.tolist())
    clean_df = combine_duplicate_headline(goog_df)
    clean_df = match_data_with_timestamp(goog_df,clean_df)
    doc2vec = encode_to_doc2vec(model, clean_df.headline, True)
    doc2vec_df = clean_df  
    doc2vec_df.headline = doc2vec
    vec2col = convert_vector_to_dataframe(doc2vec)
    doc2vec_df = pd.concat([doc2vec_df,vec2col], axis=1)
    doc2vec_df.to_csv('data/doc2vec_goog.csv', index=False)
    
    
    