"use strict";

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`${path} -> ${response.status}`);
  return response.json();
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function card(label, value) {
  const node = el("div", "card");
  node.appendChild(el("div", "value", String(value)));
  node.appendChild(el("div", "label", label));
  return node;
}

function renderSummary(result, reproduced) {
  const summary = document.getElementById("summary");
  summary.innerHTML = "";
  summary.appendChild(card("Executions", result.executions));
  summary.appendChild(card("Coverage edges", result.coverage_edges));
  summary.appendChild(card("Total crashes", result.total_crashes));
  summary.appendChild(card("Unique bugs", result.unique_crashes));
  summary.appendChild(card("Reproduced", reproduced ? "yes" : "no"));
}

function renderBuckets(result) {
  const container = document.getElementById("buckets");
  container.innerHTML = "";
  if (!result.buckets.length) {
    container.appendChild(el("p", "hint", "No crashes found for this configuration."));
    return;
  }
  const table = el("table");
  const head = el("tr");
  for (const h of ["Severity", "Exception", "Location", "Count", "Sample input"]) {
    head.appendChild(el("th", null, h));
  }
  table.appendChild(head);
  for (const bucket of result.buckets) {
    const row = el("tr");
    const sev = el("td");
    sev.appendChild(el("span", `badge ${bucket.severity}`, bucket.severity));
    row.appendChild(sev);
    row.appendChild(el("td", "mono", bucket.exception_type));
    row.appendChild(el("td", "mono", bucket.location));
    row.appendChild(el("td", null, String(bucket.count)));
    row.appendChild(el("td", "mono", bucket.sample_repr));
    table.appendChild(row);
  }
  container.appendChild(table);
}

async function submit(event) {
  event.preventDefault();
  document.getElementById("meta").textContent = "running...";
  const body = {
    protocol: document.getElementById("protocol").value,
    iterations: Number(document.getElementById("iterations").value),
    seed: Number(document.getElementById("seed").value),
    semantic_corpus: document.getElementById("semantic").checked,
  };
  const response = await api("/campaign", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  renderSummary(response.result, response.regressions_reproduced);
  renderBuckets(response.result);
  document.getElementById("meta").textContent =
    `${response.result.protocol} — seed ${response.result.seed}`;
}

async function main() {
  const data = await api("/protocols");
  const select = document.getElementById("protocol");
  for (const protocol of data.protocols) {
    const option = el("option", null, protocol);
    option.value = protocol;
    select.appendChild(option);
  }
  document.getElementById("form").addEventListener("submit", submit);
}

main().catch((error) => {
  document.getElementById("subtitle").textContent = `Failed to load: ${error.message}`;
});
