## DLS - A Energy Consumption Monitoring System For Residential Households 

Introduction
===========
This system is used to monitoring energy consumption pattern and transitions of residential households based on segmentations. Three segmentations were considered in this system, including neigborhoods customized by drawing on maps, clusterings based on daily consumption patterns, and customer grouops accoridng to their similarity of social characteristics.

 


Requirements
============

The python dependencies are managed using pip and listed in
`requirements.txt`

Setting up Local Development
============================

First, clone this repository:

    git clone https://github.com/kazuar/flask_mapbox.git

You can use pip, virtualenv and virtualenvwrapper to install the requirements:

    pip install -r requirements.txt
 
Make sure you have npm and bower installed on your machine (for javascript dependencies):

    bower install

Create `setting.py` file for the MAPBOX_ACCESS_KEY:

	MAPBOX_ACCESS_KEY = '<MAPBOX_ACCESS_KEY>'	

Start the server by running `start.sh`:

	sh start.sh
