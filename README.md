# Vulnerable Demo Server

This program is a standalone web server hosting apps vulnerable to a number of commmon web bugs.  I made this to introduce those new or interested in information security to classes of web vulnerabilities.  

** Current Modules **
- XSS (HTML injection, filter bypass, AngularJS injection)
- SQL Injection (basic, UNION attack, filter bypass)
- SSRF (PDF generation)

## Getting Started

To begin, ensure python3 is installed on the target computer, then run the following commands:
1) git clone https://www.github.com/caryhooper/vulndemoserver
2) cd vulndemoserver/
3) Install the requirements and run in Python.
	3a) python -m pip install -r requirements.txt
	3b) python vulndemoserver.py
4) Alternately, install within a pipenv with the following commands
	4a) pipenv install -r requirements.txt
	4b) pipenv run python vulndemoserver.py
5) Navigate to http://127.0.0.1:31337/
6) Happy hacking!

## Contributing

Feel free to contribute by testing, sending me feedback, or pull request.

## Authors

* **Cary Hooper** - [caryhooper](https://github.com/caryhooper)

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details

## Acknowledgments

* Thanks to Andy Acer for introducing me to CherryPy.
* Special thanks to friends and colleagues who helped me test.  

