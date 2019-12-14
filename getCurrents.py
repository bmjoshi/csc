#!/usr/bin/env python
# coding: utf-8

import sys, os
import numpy as np
import time
from datetime import datetime
import ROOT
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tdrstyle import setTDRStyle


setTDRStyle()

color_palette = [1, 901, 632, 809, 419, 600, 883];
voltageMap = {'5.5V':0,'4.0V':1,'3.0V':2}

def query(server_):
   sample = requests.get("http://emusx"+str(server_)+".cern.ch:20011/urn:xdaq-application:lid=70/DMBStatus?dmb=0")
   c = sample.content
   soup = BeautifulSoup(c, features="lxml")
   tmpstr=''
   for i in range(42,63):
      tmpstr+=(soup.find_all("td")[i].string.strip().split('=   ')[1])+','
   for i in range(69,90):
      tmpstr+=(soup.find_all("td")[i].string.strip().split('=   ')[1])
      if not (i==89): tmpstr+=','
   return tmpstr

def discreteY(ylist):
    vec = []
    vec.append(ylist[0])
    for i in range(1,len(ylist)):
        vec.append(ylist[i-1])
        vec.append(ylist[i])
    return vec

def discreteX(xlist):
    vec = []
    vec.append(xlist[0])
    for i in range(1,len(xlist)):
        for j in xrange(2): vec.append(xlist[i])
    return vec


def stepGraph(x_, y_, color_):
    if not (len(x_)==len(y_)):
        print "Lengths of the vectors don't match!!"
        return
    g_points = ROOT.TGraph(len(x_), np.array(x_), np.array(y_))
    g_line = ROOT.TGraph(len(discreteX(x_)), np.array(discreteX(x_)), np.array(discreteY(y_)))

    g_points.SetMarkerColor(color_)
    g_points.SetMarkerStyle(21)
    g_line.SetLineColor(color_)
    g_line.SetLineWidth(2)
    return (g_points, g_line)


def plot(data_, voltage_, str_):
    mulgr = ROOT.TMultiGraph();
    XMAX = []; YMAX = [];
    XMIN = []; YMIN = [];
    x_ = []
    timestamps = data_[1].tolist()
    for t in timestamps:
        tstamp = ROOT.TDatime(t)
        x_.append(float(tstamp.Convert()))
    leg = ROOT.TLegend(0.125,0.85,0.925,0.925)
    leg.SetNColumns(7)
    for cfeb_ in xrange(7):
        if (str_=='I'): index = 2+(cfeb_)*3 + voltageMap[voltage_]
        elif (str_=='V'): index = 23 + (cfeb_)*3 + voltageMap[voltage_]
        else:
            print "Unknown quantity!"
            return
        y_ = []

        y_ = data_[index].tolist()
        (gp_, gl_) = stepGraph(x_, y_, color_palette[cfeb_])
        mulgr.Add(gp_,'p')
        mulgr.Add(gl_,'l')
        leg.AddEntry(gp_,"xDCFEB "+str(cfeb_+1),'p')
        YMAX.append(max(y_))
        YMIN.append(min(y_))

    ytitle = 'xDCFEB '+str_+' ('+voltage_+')'
    if (str_=='I'): ytitle+=' [A]'
    elif (str_=='V'): ytitle+=' [V]'

    ymin = min(YMIN)-0.25*(max(YMAX)+min(YMIN))
    ymax = max(YMAX)+0.25*(max(YMAX)+min(YMIN))
    xmin = min(x_)
    xmax = max(x_)

    mulgr.GetXaxis().SetTitle("Time [s]")
    mulgr.GetYaxis().SetTitle(ytitle)

    mulgr.SetMinimum(ymin);
    mulgr.SetMaximum(ymax);
    mulgr.GetXaxis().SetLimits(xmin,xmax);
    mulgr.GetXaxis().SetTimeDisplay(1);
    mulgr.GetXaxis().SetNdivisions(-503);
    mulgr.GetXaxis().SetTimeFormat("%M:%S");
    mulgr.GetYaxis().SetNdivisions(510);
    mulgr.GetYaxis().SetLabelSize(0.05);
    mulgr.GetXaxis().SetLabelSize(0.05);
    mulgr.GetXaxis().SetTitleSize(0.06);
    mulgr.GetYaxis().SetTitleSize(0.06);
    mulgr.GetYaxis().SetTitleOffset(0.5);
    return (mulgr, leg)

def getAllPlots(filename):

    data = pd.read_csv(filename, delimiter=',', header=None)
    pdfName = filename.replace('.csv','.pdf')
    # define canvas
    c = ROOT.TCanvas("c","New Canvas",1200,1200);
    c.Divide(1,3)
    lst = []
    for num, q in enumerate(['I','V']):
        for v in voltageMap:
            index = num*3+voltageMap[v]
            print "Plotting "+q+" "+v+" "+str(index+1)
            c.cd(index+1)
            lst.append(plot(data, v, q))
            lst[index][0].Draw("a")
            lst[index][1].Draw("same")
        c.SaveAs(pdfName)

def main():
    TIME = 10 # seconds
    SERVER = 507 # {507 (FAST1), 505 (FAST2), 508 (LTT)}
    filename = getData(SERVER, TIME)
    getAllPlots(filename)

if __name__=='__main__':
   main()
