// n8n Code node — Parse Claude Sonnet Analysis Response
// Runs after the "Call Claude Sonnet" HTTP Request node in the
// Weekly Analysis workflow.
//
// Input:  Claude API response (messages endpoint)
// Output: validated analysis JSON + metadata for the analysis sheet

const response = $input.first().json;

// Extract text from Claude API response format
let rawText = '';
try {
  rawText = response.content[0].text || '';
} catch (e) {
  return [{
    json: {
      parse_error: true,
      error_detail: 'No content in Claude response',
      executive_summary: 'Analysis unavailable — Claude response was empty.',
      significant_changes: [],
      cluster_analysis: [],
      watch_list: [],
      tokens_used: response.usage?.input_tokens + response.usage?.output_tokens || 0,
    }
  }];
}

// Strip markdown code fences if Claude wrapped the JSON
rawText = rawText.replace(/^```json?\s*/m, '').replace(/\s*```$/m, '').trim();

let analysis;
try {
  analysis = JSON.parse(rawText);
} catch (e) {
  return [{
    json: {
      parse_error: true,
      error_detail: `JSON parse failed: ${e.message}`,
      raw_response: rawText.slice(0, 500),
      executive_summary: 'Analysis unavailable — response could not be parsed.',
      significant_changes: [],
      cluster_analysis: [],
      watch_list: [],
      tokens_used: (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0),
    }
  }];
}

// Validate and normalise expected fields
const result = {
  parse_error: false,
  error_detail: null,
  executive_summary: typeof analysis.executive_summary === 'string'
    ? analysis.executive_summary
    : 'No summary provided.',
  significant_changes: Array.isArray(analysis.significant_changes)
    ? analysis.significant_changes
    : [],
  cluster_analysis: Array.isArray(analysis.cluster_analysis)
    ? analysis.cluster_analysis
    : [],
  watch_list: Array.isArray(analysis.watch_list)
    ? analysis.watch_list
    : [],
  tokens_input: response.usage?.input_tokens || 0,
  tokens_output: response.usage?.output_tokens || 0,
  tokens_used: (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0),
  claude_raw_json: JSON.stringify(analysis),
};

return [{ json: result }];
