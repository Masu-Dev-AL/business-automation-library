// n8n Code node: A10 — Create Standard Onboarding Tasks
// Always runs after extracted tasks (regardless of extraction quality).
// Returns the 5 baseline onboarding tasks with due dates relative to start_date_resolved.
// Each task is tagged task_source: standard for the audit log.

const data = $('A6 - Assess Extraction Quality').first().json;
const startDate = new Date(data.start_date_resolved);

function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result.toISOString().slice(0, 10);
}

const standardTasks = [
  {
    task_name: 'Send welcome packet to client',
    due_date: addDays(startDate, 1),
    assignee_name: 'Account Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Account Manager'
  },
  {
    task_name: 'Schedule kickoff call',
    due_date: addDays(startDate, 2),
    assignee_name: 'Account Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Account Manager'
  },
  {
    task_name: 'Set up client workspace/folder',
    due_date: addDays(startDate, 1),
    assignee_name: 'Project Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Project Manager'
  },
  {
    task_name: 'Confirm deliverable timeline with client',
    due_date: addDays(startDate, 3),
    assignee_name: 'Project Manager',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Project Manager'
  },
  {
    task_name: 'Internal project briefing',
    due_date: addDays(startDate, 2),
    assignee_name: 'Full Team',
    task_source: 'standard',
    contract_id: data.contract_id,
    deliverable_ref: 'Onboarding',
    notes: 'Assignee Placeholder: Full Team'
  }
];

return standardTasks.map(task => ({ json: task }));
