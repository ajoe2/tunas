# swimdatabase
`swimdatabase` is an application that analyzes USA Swimming meet results and applies them to various uses. It is useful for

 - Individual time search
 - Club information
 - Time Standards
 - Automatic relay generation

### Built with
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)

## Getting started
### Prerequisites
This project is built for MacOS. There are no guarentees on whether it will run on other operating systems.

All the code is written using Python. To download Python, follow the instructions [here](https://www.python.org/downloads/).

This project relies on the `pandas` Python library. To download `pandas`, follow [these](https://pandas.pydata.org/docs/getting_started/install.html) instructions.

Note: `pandas` can be downloaded via `pip`:

```sh
    pip install pandas
```

### Installation and use
1. Open Terminal
2. Install Python and `pandas`
3. Clone the repository
```sh
    git clone https://github.com/ajoe2/swimdatabase.git
```
4. Run main.py
```sh
    cd swimdatabase/src
    python3 main.py
```

### Example output
```
#############################################################
##########              Swim Database              ##########
#############################################################
Version: 1.0.0

Files processed:   *************************************|100%
Finished processing files!
-------------------------------------------------------------

1) Swimmer information
2) Time standards
3) Club information
4) Relay mode
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
 --> Club:        PCSCSC
 --> Age Group:   10&u
 --> Sex:         Female
 --> Course:      SCY
 --> Date:        2024-12-05
 --> Num relays:  2

Update field:
 1) Club
 2) Age group
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

Selection > 2

4x50 Freestyle Relay SCY 'A' [1:52.61] AAAA
 Free    Wang, Amy                     10  8FCE4D1BA4E52A  PCSCSC    26.72  AAAA  2024 Pacific Swimming Winter A
 Free    Jia, Annabelle A              10  B6EB9FB8C8E742  PCSCSC    27.70  AAAA  Milpitas Aquatic Club SC CBA+ 
 Free    Poon, Olivia                  10  4DA8229D8C2046  PCSCSC    28.96  AAA   2024 Pacific Swimming Winter A
 Free    Mosendz, Sophia               10  5186BC1BE78A4A  PCSCSC    29.23  AAA   2024 Pacific Swimming Winter A

4x50 Freestyle Relay SCY 'B' [2:06.21] AAA
 Free    Alise, Savannah R             10  83D133E17AEE4F  PCSCSC    30.60  AA    MBSC/GSMY Z1S Race to AGC C/B/
 Free    Xu, Evelyn L                   9  0C1A7BB2D8F642  PCSCSC    31.14  AGC   GGST Spooktacular             
 Free    Zhou, Hannah                  10  214A614D34DB44  PCSCSC    32.15  BB    Folsom Classic 2024           
 Free    Li, Shuyi                     10  E2282DD45E4D47  PCSCSC    32.32  BB    Zone 1 South Winter Championsh

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

4x50 Medley Relay: SCY 'A' [2:03.31] AAAA
 Back    Jia, Annabelle A              10  B6EB9FB8C8E742  PCSCSC    31.87  AAAA  Folsom Classic 2024           
 Breast  Alise, Savannah R             10  83D133E17AEE4F  PCSCSC    34.90  AAAA  2024 Pacific Swimming Winter A
 Fly     Poon, Olivia                  10  4DA8229D8C2046  PCSCSC    29.82  AAAA  2024 Pacific Swimming Winter A
 Free    Wang, Amy                     10  8FCE4D1BA4E52A  PCSCSC    26.72  AAAA  2024 Pacific Swimming Winter A

4x50 Medley Relay: SCY 'B' [2:18.07] AAA
 Back    Tran, Hong-An                 10  7F8833F98F2D48  PCSCSC    37.46  A     2024 Pacific Swimming Winter A
 Breast  Zhou, Hannah                  10  214A614D34DB44  PCSCSC    38.07  AAA   Folsom Classic 2024           
 Fly     Xu, Evelyn L                   9  0C1A7BB2D8F642  PCSCSC    33.31  FW    Folsom Classic 2024           
 Free    Mosendz, Sophia               10  5186BC1BE78A4A  PCSCSC    29.23  AAA   2024 Pacific Swimming Winter A

Selection >
```
