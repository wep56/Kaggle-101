import pandas as pd
import numpy as np
import re
from sklearn.ensemble import RandomForestRegressor
from sklearn import preprocessing
path="C:\\Users\\wei\\Desktop\\Kaggle\\Kaggle101\\Titanic\\"  
pd.set_option('precision', 4) 
    ########################step1:import the data#################################################    
def loadDataFrame():
    train_df=pd.read_csv(path+'train.csv')
    test_df=pd.read_csv(path+'test.csv')
    df=pd.concat([train_df,test_df])
    df.reset_index(inplace=True)
    df.drop('index',axis=1,inplace=True)
    #merge the train DataFrame and the test DataFrame because we 
    #need more data to do statical things
    #reindex the columns to be the columns in the training data
    df=df.reindex_axis(train_df.columns,axis=1)
    print df.shape[1],"columns:",df.columns.values
    print "Row count:",df.shape[0]
    return train_df,test_df,df

    ######################step2:generating individual features from raw data###########################################
###Generate feature from the 'Plclass' variable
def processPclass(df,keep_binary=False,keep_scaled=False):
    #fill in the missing value
    df['Pclass'][df.Pclass.isnull()]=df['Pclass'].median()
    #create binary features
    if keep_binary:
        df=pd.concat([df,pd.get_dummies(df['Pclass']).rename(columns=lambda x:'Pclass_'+str(x))],axis=1)
    if keep_scaled:
        scaler=preprocessing.StandardScaler()
        df['Pclass_scaled']=scaler.fit_transform(df['Pclass'])
    return df

###Generate features from the 'Name' variable
def processName(df,keep_binary=False,keep_scaled=False,keep_bins=False):
    """
    Parameters:
        keep_binary:include 'Title_Mr' 'Title_Mrs'...
        keey_scaled&&keep_bins:include 'Names_scaled' 'Title_id_scaled'
    Note: the string feature 'Name' can be deleted
    """
    # how many different names do they have? this feature 'Names'
    df['Names']=df['Name'].map(lambda x:len(re.split('\\(',x)))
    
    #what is each person's title? 
    df['Title']=df['Name'].map(lambda x:re.compile(", (.*?)\.").findall(x)[0])
    #group low-occuring,related titles together
    df['Title'][df.Title == 'Jonkheer'] = 'Master'
    df['Title'][df.Title.isin(['Ms','Mlle'])] = 'Miss'
    df['Title'][df.Title == 'Mme'] = 'Mrs'
    df['Title'][df.Title.isin(['Capt', 'Don', 'Major', 'Col', 'Sir','Rev'])] = 'Sir'
    df['Title'][df.Title.isin(['Dona', 'Lady', 'the Countess'])] = 'Lady'
    #build binary features
    if keep_binary:
        df=pd.concat([df,pd.get_dummies(df['Title']).rename(columns=lambda x:'Title_'+str(x))],axis=1)
    #process_scaled
    if keep_scaled:
        scaler=preprocessing.StandardScaler()
        df['Names_scaled']=scaler.fit_transform(df['Names'])
    if keep_bins:
        df['Title_id']=pd.factorize(df['Title'])[0]+1
        del df['Title']
    if keep_bins and keep_scaled:
        scaler=preprocessing.StandardScaler()
        df['Title_id_scaled']=scaler.fit_transform(df['Title_id'])
    del df['Name']
    return df

###Generate feature from 'Sex' variable
def processSex(df):
    df['Gender'] = np.where(df['Sex'] == 'male', 1, 0)
    del df['Sex']
    return df

###Generate feature from 'SibSp' and 'Parch'
def processFamily(df,keep_binary=False,keep_scaled=False):
    #interaction variables require no zeros ,lift up everything
    df['SibSp']=df['SibSp']+1
    df['Parch']=df['Parch']+1
    if keep_binary:
        sibsps=pd.get_dummies(df['SibSp']).rename(columns=lambda x:'SibSp_'+str(x))
        parchs=pd.get_dummies(df['Parch']).rename(columns=lambda x:'Parch_'+str(x))
        df=pd.concat([df,sibsps,parchs],axis=1)
    if keep_scaled:
        scaler=preprocessing.StandardScaler()
        df['SibSp_scaled']=scaler.fit_transform(df['SibSp'])
        df['Parch_scaled']=scaler.fit_transform(df['Parch'])
    return df
    
###Generate features from 'Ticket' variable
###Utility method: get the index of 'Ticket'
def getTicketPrefix(ticket):
    match=re.compile("([a-zA-Z\.\/]+)").search(ticket)
    if match:
        return match.group(0)
    else:
        return 'U'

###Utility method: get the numerical component of 'Ticket'
def getTicketNumber(ticket):
    match=re.compile("([0-9]+)").search(ticket)
    if match:
        return match.group(0)
    else:
        return '0'
###Generate features of 'Ticket'
def processTicket(df,keep_binary=False,keep_bins=False,keep_scaled=False):
    df['TicketPrefix']=df['Ticket'].map(lambda x:getTicketPrefix(x.upper()))
    df['TicketPrefix']=df['TicketPrefix'].map(lambda x:re.sub('[\.?\/?]','',x))
    df['TicketPrefix']=df['TicketPrefix'].map(lambda x:re.sub('STON','SOTON',x))
    
    df['TicketNumber']=df['Ticket'].map(lambda x:getTicketNumber(x))
    df['TicketNumberStart']=df['TicketNumber'].map(lambda x:x[0]).astype(np.int)
    
    if keep_binary:
        numberstart = pd.get_dummies(df['TicketNumberStart']).rename(columns=lambda x: 'TicketNumberStart_' + str(x))
        df = pd.concat([df, numberstart], axis=1)
    if keep_bins:
        #help the interactive feature process,lift by 1
        df['TicketPrefix_id']=pd.factorize(df['TicketPrefix'])[0]+1      
    if keep_scaled:
        scaler = preprocessing.StandardScaler()
        df['TicketNumber_scaled'] = scaler.fit_transform(df['TicketNumber'])
        df['TicketPrefix_id_scaled'] = scaler.fit_transform(df['TicketPrefix_id'])
    del df['Ticket'],df['TicketNumber'],df['TicketPrefix'],df['TicketNumberStart'],df['TicketPrefix_id']
    return df

###Generate features from 'Fare'--Ticket Price
def processFare(df,keep_binary=False,keep_bins=False,keep_scaled=False):
    #replace missing values with the median
    df['Fare'][df.Fare.isnull()]=df['Fare'].median()
    #lift zeros values to 1/10 of the minium because we will add interactive features
    df['Fare'][np.where(df['Fare']==0)[0]]=df['Fare'][df['Fare'].nonzero()[0]].min()/10
    #bin into quantilies for binary features
    if keep_bins:
        df['Fare_bin']=pd.qcut(df['Fare'],4)
        df['Fare_bin_id']=pd.factorize(df['Fare_bin'])[0]+1
    if keep_binary:
        df=pd.concat([df,pd.get_dummies(df['Fare_bin']).rename(columns=lambda x:'Fare_bin_'+str(x))],axis=1)
    if keep_scaled:
        scaler=preprocessing.StandardScaler()
        df['Fare_scaled']=scaler.fit_transform(df['Fare'])
    if keep_bins and keep_scaled:
        scaler = preprocessing.StandardScaler()
        df['Fare_bin_id_scaled'] = scaler.fit_transform(df['Fare_bin_id'])
        del df['Fare_bin'],df['Fare_bin_id']
    return df   

###Generate features from 'Cabin'
#Utility method 
def getCabinLetter(cabin):
    match = re.compile("([a-zA-Z]+)").search(cabin)
    if match:
        return match.group(0)
    else:
        return 'U'
        
#Utility method
def getCabinNumber(cabin):
    match = re.compile("([0-9]+)").search(cabin)
    if match:
        return match.group(0)
    else:
        return 0

def processCabin(df,keep_binary=False,keep_scaled=False):   
    # Replace missing values with "U0"
    df['Cabin'][df.Cabin.isnull()] = 'U0'   
    # create feature for the alphabetical part of the cabin number
    df['CabinLetter'] = df['Cabin'].map( lambda x : getCabinLetter(x)) 
    # create binary features for each cabin letters
    if keep_binary:
        #change alphbet to number beacause we need tht important feature to regress the age
        df['CabinLetter']=pd.factorize(df['CabinLetter'])[0]
        cletters = pd.get_dummies(df['CabinLetter']).rename(columns=lambda x: 'CabinLetter_' + str(x))
        df = pd.concat([df, cletters], axis=1)  
    # create feature for the numerical part of the cabin number
    df['CabinNumber'] = df['Cabin'].map( lambda x : getCabinNumber(x)).astype(int) + 1
    # scale the number to process as a continuous feature
    if keep_scaled:
        scaler = preprocessing.StandardScaler()
        df['CabinNumber_scaled'] = scaler.fit_transform(df['CabinNumber'])
        df['CabinLetter_scaled'] = scaler.fit_transform(df['CabinLetter'])
        del df['Cabin'],df['CabinNumber']
    return df

###Generate feature from 'Embarked'
def processEmbarked(df,keep_binary=False,keep_scaled=False):
    #replace the missing values with most common port
    df['Embarked'][df['Embarked'].isnull()]=df.Embarked.dropna().mode().values
    #turn into number
    df['Embarked']=pd.factorize(df['Embarked'])[0]
    # Create binary features for each port
    if keep_binary:
        df = pd.concat([df, pd.get_dummies(df['Embarked']).rename(columns=lambda x: 'Embarked_' + str(x))], axis=1)
    if keep_scaled:
        scaler=preprocessing.StandardScaler()
        df['Embarked_scaled']=scaler.fit_transform(df['Embarked'])
    return df

###Generate feature from 'Age'--the most important feature
#Utility method:fill missing ages using a RandomForestClassifier
def setMissingAges(df):
    age_df=df[['Age','Embarked','Fare','Parch','SibSp','Title_id','Pclass','Names','CabinLetter']]
    knownAge=age_df[df.Age.notnull()]
    unknownAge=age_df[df.Age.isnull()]
    y=knownAge.values[:,0]
    X=knownAge.values[:,1:]
    rfr=RandomForestRegressor(n_estimators=2000,n_jobs=-1)
    #train the regressor
    rfr.fit(X,y)
    predictedAges=rfr.predict(unknownAge.values[:,1:])
    df['Age'][df.Age.isnull()]=predictedAges
    return df

def processAge(df,keep_binary=False,keep_bins=False,keep_scaled=False):
    df=setMissingAges(df)
    # have a feature for children
    df['isChild'] = np.where(df.Age < 13, 1, 0)
    # bin into quantiles and create binary features
    df['Age_bin'] = pd.qcut(df['Age'], 4)
    if keep_binary:
        df = pd.concat([df, pd.get_dummies(df['Age_bin']).rename(columns=lambda x: 'Age_' + str(x))], axis=1)  
    if keep_scaled:
        scaler=preprocessing.StandardScaler()
        df['Age_scaled']=scaler.fit_transform(df['Age'])
    del df['Age_bin']
    return df
###Delete the not useful columns
def processDrops(df):
    DropList =['Age','Embarked','Fare','Parch','SibSp','Title_id','Pclass','Names','CabinLetter']
    df.drop(DropList, axis=1, inplace=True)
    return df

def getData():
    train_df,test_df,df=loadDataFrame()
    # generate features from individual variables present in the raw data
    df=processPclass(df,keep_binary=True,keep_scaled=True)
    df=processName(df,keep_binary=True,keep_bins=True,keep_scaled=True)
    df=processSex(df)
    df=processFamily(df,keep_scaled=True)
    df=processTicket(df,keep_binary=True,keep_bins=True,keep_scaled=True)
    df=processFare(df,keep_scaled=True)
    df=processCabin(df,keep_binary=True,keep_scaled=True)
    df=processEmbarked(df,keep_binary=True,keep_scaled=True)
    df=processAge(df,keep_binary=True,keep_bins=True,keep_scaled=True)
    df=processDrops(df)
    print "Starting with", df.columns.size, "manually generated features...\n", df.columns.values
    ##########################Step3:add interactive features###################
    numerics=df[['Names_scaled','SibSp_scaled','Parch_scaled','TicketPrefix_id_scaled','Fare_scaled','CabinNumber_scaled',
                 'Pclass_scaled','Title_id_scaled','TicketNumber_scaled','CabinLetter_scaled','Embarked_scaled','Age_scaled']]
    print "\nFeatures used for automated feature generation:\n", numerics.head(10)
    new_fields_count=0
    for i in range(0,numerics.columns.size-1):
        for j in range(0,numerics.columns.size-1):
            """
            if i<=j:
                name=str(numerics.columns.values[i])+'*'+str(numerics.columns.values[j])
                df=pd.concat([df,pd.Series(numerics.iloc[:,i]*numerics.iloc[:,j],name=name)],axis=1)
                new_fields_count+=1
            if i < j:
                name = str(numerics.columns.values[i]) + "+" + str(numerics.columns.values[j])
                df = pd.concat([df, pd.Series(numerics.iloc[:,i] + numerics.iloc[:,j], name=name)], axis=1)
                new_fields_count += 1
            
            if not i == j:
                name = str(numerics.columns.values[i]) + "/" + str(numerics.columns.values[j])
                df = pd.concat([df, pd.Series(numerics.iloc[:,i] / numerics.iloc[:,j], name=name)], axis=1)
           
                name = str(numerics.columns.values[i]) + "-" + str(numerics.columns.values[j])
                df = pd.concat([df, pd.Series(numerics.iloc[:,i] - numerics.iloc[:,j], name=name)], axis=1)
                new_fields_count += 2     
            """
    print "\n", new_fields_count, "new features generated"
    ################################Step4:Remove highly correlated features#########################
    df_corr=df.drop(['Survived','PassengerId'],axis=1).corr(method='spearman')
    mask=np.ones(df_corr.columns.size)-np.eye(df_corr.columns.size)
    df_corr=df_corr*mask
    drops=[]
    for col in df_corr.columns.values:
        if np.in1d([col],drops):
            continue
        corr=df_corr.index[abs(df_corr[col])>0.9].values
        drops=np.union1d(drops,corr)
    print "\nDropping",drops.shape[0],"highly correlated features"
    df.drop(drops,axis=1,inplace=True)
    
    train_df=df[:train_df.shape[0]]
    test_df=df[train_df.shape[0]:]
    test_df.reset_index(inplace=True)
    test_df.drop('index',axis=1,inplace=True)
    test_df.drop('Survived',axis=1,inplace=1)
    return train_df,test_df

if __name__=='__main__':
    train_df,test_df=getData()
    drop_list=['PassengerId']
    train_df.drop(drop_list,axis=1,inplace=1)
    test_df.drop(drop_list,axis=1,inplace=1)
    print "1 training label and %d training  features:\n %s " %(train_df.columns.size-1,train_df.columns.values)
    print "\n\n %d test features:\n%s" %(test_df.columns.size,test_df.columns.values)