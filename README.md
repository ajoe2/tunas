# Tunas: data analysis for competitive swimming
`tunas` is a Python CLI for analyzing USA Swimming meet results.

### Features
 - Individual time search
 - Club information
 - Time standard information
 - Relay generation

### Built with
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas)](https://pandas.pydata.org/)

## Getting started
### Prerequisites
All the code is written using Python. To download Python, follow the instructions [here](https://www.python.org/downloads/). Make sure you have Python version 3.12 or above.

To check that you have successfully installed Python, you can run
```sh
python3 --version
```
or 
```sh
python3 -V
```
which will display the downloaded Python version (ex. `Python 3.12.10`).

To clone the repository, you will need to use `git`. You can follow the instructions [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) to install it if you haven't already.

### Installation and use
1. Clone the repository.
```sh
    git clone https://github.com/ajoe2/tunas.git
```
2. `cd` into the tunas project directory
```sh
    cd tunas
```
3. Install the necessary dependencies by running
```sh
    pip install -r requirements.txt
```
4. Execute `python3 tunas`
```sh
    python3 tunas
```

### Example output
```
#############################################################
##########           Tunas: Data Analysis          ##########
#############################################################
Version: 1.1.0

Loading files...
Files read: 384
Finished processing files!
-------------------------------------------------------------

1) Swimmer information
2) Time standards
3) Club information
4) Relay mode
5) Database statistics
Quit (q/Q)

Select mode > 4

1) Settings
2) 4 x 50 Free
3) 4 x 50 Medley
4) 4 x 100 Free
5) 4 x 100 Medley
6) 4 x 200 Free
7) Exclude swimmer
8) Include swimmer
Back (b/B)

Selection > 1

Query settings:
 * Club:        PC-SCSC
 * Age range:   1-10
 * Sex:         Female
 * Course:      LCM
 * Date::       2025-06-08
 * Num relays:  2

1) Club
2) Age range
3) Sex
4) Course
5) Date
6) Num relays
Back (b/B)

Selection > b

1) Settings
2) 4 x 50 Free
3) 4 x 50 Medley
4) 4 x 100 Free
5) 4 x 100 Medley
6) 4 x 200 Free
7) Exclude swimmer
8) Include swimmer
Back (b/B)

Selection > 3

4x50 Medley Relay LCM: 'A' [2:31.43] [AAAA]
 Back    Irene Zhong                 10  F  49AC52F6961843  PC-SCSC     37.11  AAAA  2024 Long Course Far Western C
 Breast  Hannah Zhou                 10  F  214A614D34DB44  PC-SCSC     42.45  AAA   Zone 1 South May Firecracker 5
 Fly     Evelyn L Xu                 10  F  0C1A7BB2D8F642  PC-SCSC     35.84  AAA   Zone 1 South May Firecracker 5
 Free    Lydia Xiao                  10  F  DE68CFBFBCA24E  PC-SCSC     36.03  A     Zone 1 South May Firecracker 5

4x50 Medley Relay LCM: 'B' [2:50.72] [AA]
 Back    Grace Liu                    8  F  311185068D104B  PC-SCSC     43.96  BB    Zone 1 South May Firecracker 5
 Breast  Chloe Chai                   8  F  C62C0364984B46  PC-SCSC     48.84  BB    Zone 1 South May Firecracker 5
 Fly     Ellie Y Wang                 8  F  D145A5E5619F4A  PC-SCSC     40.44  AGC   Zone 1 South May Firecracker 5
 Free    Kensie A Gray               10  F  45400F9C07CE40  PC-SCSC     37.48  BB    Zone 1 South May Firecracker 5

1) Settings
2) 4 x 50 Free
3) 4 x 50 Medley
4) 4 x 100 Free
5) 4 x 100 Medley
6) 4 x 200 Free
7) Exclude swimmer
8) Include swimmer
Back (b/B)

Selection > 1

Query settings:
 * Club:        PC-SCSC
 * Age range:   1-10
 * Sex:         Female
 * Course:      LCM
 * Date::       2025-06-08
 * Num relays:  2

1) Club
2) Age range
3) Sex
4) Course
5) Date
6) Num relays
Back (b/B)

Selection > 3

1) Female
2) Male
Back (b/B)

Selection > 2
Success! New sex set to: Male

Query settings:
 * Club:        PC-SCSC
 * Age range:   1-10
 * Sex:         Male
 * Course:      LCM
 * Date::       2025-06-08
 * Num relays:  2

1) Club
2) Age range
3) Sex
4) Course
5) Date
6) Num relays
Back (b/B)

Selection > b

1) Settings
2) 4 x 50 Free
3) 4 x 50 Medley
4) 4 x 100 Free
5) 4 x 100 Medley
6) 4 x 200 Free
7) Exclude swimmer
8) Include swimmer
Back (b/B)

Selection > 3

4x50 Medley Relay LCM: 'A' [2:28.67] [AAAA]
 Back    Albert Y Xiao               10  M  4FDE9748521045  PC-SCSC     38.21  AAAA  Zone 1 South May Firecracker 5
 Breast  Jeffrey Sun                 10  M  08371C3623774C  PC-SCSC     40.72  AAAA  Zone 1 South May Firecracker 5
 Fly     Anay S Datar                10  M  E534B8D6B1104F  PC-SCSC     36.17  AAAA  2024 Long Course Far Western C
 Free    Rubix V Szolusha             9  M  06CF768B99D541  PC-SCSC     33.57  FW    Zone 1 South May Firecracker 5

4x50 Medley Relay LCM: 'B' [2:39.44] [AAAA]
 Back    Aurelius Y Lien              8  M  06150ED6FD1743  PC-SCSC     40.21  FW    Zone 1 South May Firecracker 5
 Breast  Adam J Li                   10  M  4616CAFDEB2347  PC-SCSC     47.90  BB    Zone 1 South May Firecracker 5
 Fly     Lucas W Zhou                10  M  38D321F7DDAF4A  PC-SCSC     36.68  FW    Zone 1 South May Firecracker 5
 Free    Lucas Guo                   10  M  A05D75DB613044  PC-SCSC     34.65  AGC   Zone 1 South May Firecracker 5
```
