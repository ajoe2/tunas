# Tunas: data analysis for competitive swimming
`tunas` is a Python CLI for analyzing USA Swimming meet results. It can also be used as a library for data analysis.

### Features
 - Individual time search
 - Club information
 - Time Standards
 - Relay generation

### Built with
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas)](https://pandas.pydata.org/)

## Getting started
### Prerequisites
All the code is written using Python. To download Python, follow the instructions [here](https://www.python.org/downloads/). The recommended version is Python 3.12.

This project uses the `pandas` Python library. To download `pandas`, run
```sh
    pip3 install pandas
```
after downloading Python.

### Installation and use
1. Clone the repository
```sh
    git clone https://github.com/ajoe2/tunas.git
```
2. Run tunas
```sh
    cd tunas
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
 * Age range:   7-10
 * Sex:         Female
 * Course:      SCY
 * Date::       2025-06-05
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

4x50 Medley Relay SCY: 'A' [2:16.16]
 Back    Nandika Singh         10        C826B07D9D4E41  PC-SCSC  37.11     Pacific Swimming 10 & Under SC
 Breast  Hannah Zhou           10        214A614D34DB44  PC-SCSC  35.99     Spring SCY Age Group Champions
 Fly     Evelyn L Xu           10        0C1A7BB2D8F642  PC-SCSC  30.91     Spring SCY Age Group Champions
 Free    Ellie Y Wang          8         D145A5E5619F4A  PC-SCSC  32.15     2025 Brian Malick Memorial Z1S

4x50 Medley Relay SCY: 'B' [2:29.94]
 Back    Eloise M Kosiba       10        CDBF178D7A3148  PC-SCSC  38.76     Pacific Swimming 10 & Under SC
 Breast  Lydia Xiao            10        DE68CFBFBCA24E  PC-SCSC  40.41     2025 Pacific Swimming Zone All
 Fly     Chloe Chai            8         C62C0364984B46  PC-SCSC  37.60     Pacific Swimming 10 & Under SC
 Free    Grace Liu             8         311185068D104B  PC-SCSC  33.17     2025 Pacific Swimming Zone All

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
 * Age range:   7-10
 * Sex:         Female
 * Course:      SCY
 * Date::       2025-06-05
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

Selection > 2
Success! New sex set to: Male

Query settings:
 * Club:        PC-SCSC
 * Age range:   7-10
 * Sex:         Male
 * Course:      SCY
 * Date::       2025-06-05
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

4x50 Medley Relay SCY: 'A' [2:04.58]
 Back    Albert Y Xiao         10        4FDE9748521045  PC-SCSC  31.45     Pacific Swimming SC Far Wester
 Breast  Jeffrey Sun           10        08371C3623774C  PC-SCSC  33.17     Pacific Swimming SC Far Wester
 Fly     Anay S Datar          10        E534B8D6B1104F  PC-SCSC  31.23     Pacific Swimming SC Far Wester
 Free    Lucas W Zhou          10        38D321F7DDAF4A  PC-SCSC  28.73     2025 Pacific Swimming Zone All

4x50 Medley Relay SCY: 'B' [2:18.25]
 Back    Rubix V Szolusha      9         06CF768B99D541  PC-SCSC  32.87     Pacific Swimming SC Far Wester
 Breast  Aurelius Y Lien       8         06150ED6FD1743  PC-SCSC  39.57     Pacific Swimming 10 & Under SC
 Fly     Ethan S Kang          10        9FDC4D64878B86  PC-SCSC  34.12     Santa Clara Swim Club Race to 
 Free    Yuri Evstigneev       10        EE03882BB7FC4F  PC-SCSC  31.69     Pacific Swimming 10 & Under SC
```
