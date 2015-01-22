import rf
import gbdt
import svc
import numpy as np
import csv
path="C:\\Users\\wei\\Desktop\\Kaggle\\Kaggle101\\Titanic\\" 

if __name__=='__main__':
    test_ids,ret1=rf.Titanic_rf()
    test_ids,ret2=gbdt.Titanic_gbdt()
    test_ids,ret3=svc.Titanic_svc()
    ret1=np.where(ret1==1,3,0)
    ret2=np.where(ret2==1,2,0)
    ret3=np.where(ret3==1,2,0)
    votes=ret1+ret2+ret3
    votes=np.where(votes>=4,1,0)
    submission=np.asarray(zip(test_ids,votes)).astype(int)
    #ensure passenger IDs in ascending order
    output=submission[submission[:,0].argsort()]
    predict_file=open(path+"predict.csv",'wb')
    file_object=csv.writer(predict_file)
    file_object.writerow(["PassengerId","Survived"])
    file_object.writerows(output)
    predict_file.close()
    print 'Done'