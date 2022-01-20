import argparse
import pandas as pd
import sdnist
import privacy_metric
import matplotlib.pyplot as plt
import numpy as np



if __name__ == "__main__":
    parser = argparse.ArgumentParser()   
    parser.add_argument("--dataset", type=argparse.FileType("r"), help="this is the synthetic dataset (.csv file)")
    parser.add_argument("--groundtruth", type=argparse.FileType("r"), help="this is the original dataset (.csv file)")
    parser.add_argument("--privacy-metric", dest="privacy_metric", type=bool, help="compute the privacy metric")
    parser.add_argument("-x", "--exclude-columns", dest="x", help="list of columns to exclude") 
    parser.add_argument("-q", "--quasi", dest="q", help="list of quasi columns ")
   
    args = parser.parse_args()
    
    # Load datasets 
    dataset = pd.read_csv(args.dataset)  
    #groundtruth = pd.read_csv(args.groundtruth, dtypye=dtypes)
    groundtruth = pd.read_csv(args.groundtruth)
    
    
    q = args.q
    Qs = q.split(",")
    Qs = [s.strip(" ") for s in Qs]
    x = args.x
    Xs = x.split(",")
    Xs = [s.strip(" ") for s in Xs]
    percents, uniques1, uniques2, matched  = privacy_metric.cellchange(groundtruth, dataset, Qs, Xs)
    
    #Histogram
    plt.figure(figsize = (10,10))
    plt.title('Percentage of raw synthetic records that had an apparent match with groundtruth dataset')
    percents.hist()
    plt.xlim(0,100)
    plt.show()
