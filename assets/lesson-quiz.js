document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-quiz]").forEach((quiz) => {
    const button = quiz.querySelector("button");
    const feedback = quiz.querySelector("[data-feedback]");

    if (!button || !feedback) return;

    button.addEventListener("click", () => {
      const answer = quiz.querySelector("input[type='radio']:checked");

      if (!answer) {
        feedback.textContent = "先选一个答案，再检查。";
        feedback.dataset.state = "retry";
        return;
      }

      const correct = answer.dataset.correct === "true";
      feedback.textContent = correct
        ? quiz.dataset.correctFeedback || "回答正确。"
        : quiz.dataset.retryFeedback || "再想一想，然后重试。";
      feedback.dataset.state = correct ? "correct" : "retry";
    });
  });
});
