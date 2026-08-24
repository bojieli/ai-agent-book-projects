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
        ? "正确。阅读的单位不是“章”，而是“能在项目里验证的机制”。"
        : "再想想：哪种读法能让你马上得到环境反馈，并暴露理解偏差？";
      feedback.dataset.state = correct ? "correct" : "retry";
    });
  });
});
