# Service recommender testing

In the file `service_rec_test_cases.py` you can find test cases for testing the quality of the free text recommendations of the Service Match Engine microservice. You can modify existing test cases by adding new suitable services for them available in PTV (and in our database) or creating completely new test cases.

You can run test cases by executing `run_recommender_testing.py` file with Python. Remember to install required Python libraries in the `requirements.txt` at first!

The code expects that the Service Match Engine microservice is available at `http://localhost/services/recommend` but you can modify that URL accordingly in the code.

You can specify a few arguments for executing the `run_recommender_testing.py` script:
- `--language` for setting language used for testing ('fi', 'en', 'sv')
- `--recommenders_to_test` for setting recommenders used for testing ('all', 'nlp', 'lexical'). Can be one or more at the same time
- `--top_k` for setting top_k recommendations used for testing (default is 15)
- `--plot_images` for plotting test case visualizations while running the code (default is False).
- `--save_test_scores` for saving file where all test case scores are saved in addition to logging them during the code execution.

# Service recommender optimization

You can run automatic recommender parameter optimization by executing `run_recommender_optimization.py` file with Python. Remember to install required Python libraries in the `requirements.txt` at first!

At the moment, only `lexical` and `all` recommenders can be optimized since we can only optimize Lexical Text Search's BM25 parameters.

The code expects that the Lexical Text Search microservice is available at `http://localhost:3001` but you can modify that URLs accordingly in the code.

You can specify a few arguments for executing the `run_recommender_optimization.py` script:
- `--language` for setting language to optimize ('fi', 'en', 'sv')
- `--recommender_to_optimize` for setting which recommeder to optimize ('all', 'lexical')
- `--top_k` for setting top_k recommendations used in optimization (default is 15)
- `--n_trials` for setting number of trials used in optimization (default is 30)
- `--save_optimization_result` for saving file where optimization results are saved in addition to logging them during the code execution.