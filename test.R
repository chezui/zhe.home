# This fits various models on mtcars

library(tidymodels)

# Load data
data("mtcars")

# Split data
set.seed(123)

# Fit logistic regression
logistic_spec <- logistic_reg() %>%
  set_engine("glm") %>%
  set_mode("classification")

logistic_fit <- fit(logistic_spec, am ~ ., data = mtcars)


# Fit random forest