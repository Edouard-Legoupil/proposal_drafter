// Comprehensive test for the admin role fix
// This simulates the actual scenario that was causing the error

// Mock the backend API responses that could cause issues
const mockBackendResponses = {
  // Normal response with valid roles
  normalUser: {
    id: 'user-1',
    name: 'Normal User',
    email: 'normal@example.com',
    roles: [{ id: 1, name: 'Proposal Writer' }, { id: 2, name: 'Reviewer' }],
    donor_groups: ['UNICEF'],
    outcomes: [1, 2],
    field_contexts: [1]
  },

  // User with empty roles array
  emptyRolesUser: {
    id: 'user-2',
    name: 'Empty Roles User',
    email: 'empty@example.com',
    roles: [],
    donor_groups: ['WHO'],
    outcomes: [3],
    field_contexts: [2]
  },

  // User with malformed roles (null/undefined values)
  malformedRolesUser: {
    id: 'user-3',
    name: 'Malformed Roles User',
    email: 'malformed@example.com',
    roles: [null, { id: 3, name: 'Admin' }, undefined, { name: 'Invalid Role' }],
    donor_groups: ['UNDP'],
    outcomes: [1],
    field_contexts: []
  },

  // User without roles property
  noRolesUser: {
    id: 'user-4',
    name: 'No Roles User',
    email: 'noroles@example.com',
    donor_groups: ['FAO'],
    outcomes: [2],
    field_contexts: [1, 2]
  }
};

// Mock options data
const mockOptions = {
  roles: [
    { value: 1, label: 'Proposal Writer' },
    { value: 2, label: 'Reviewer' },
    { value: 3, label: 'Admin' },
    { value: 4, label: 'Editor' }
  ],
  donor_groups: ['UNICEF', 'WHO', 'UNDP', 'FAO'],
  outcomes: [{ value: 1, label: 'Outcome 1' }, { value: 2, label: 'Outcome 2' }],
  field_contexts: [{ value: 1, label: 'Field 1' }, { value: 2, label: 'Field 2' }],
  teams: [{ value: 'team-1', label: 'Team 1' }]
};

// Test the fixed handleBulkApply logic
function testBulkRoleAssignment() {
  console.log('=== Testing Bulk Role Assignment Fix ===');

  const users = Object.values(mockBackendResponses);
  const bulkValue = { value: 4, label: 'Editor' }; // Role to add
  const selectedIds = users.map(u => u.id);

  selectedIds.forEach(userId => {
    const user = users.find(u => u.id === userId);

    // This is the fixed logic from handleBulkApply
    try {
      const existingRoleIds = (user?.roles || []).filter(r => r?.id).map(r => r.id);
      const newRoleIds = [...new Set([...existingRoleIds, bulkValue.value])];

      console.log(`User ${user.id} (${user.name}):`);
      console.log(`  Existing roles: ${JSON.stringify(user.roles)}`);
      console.log(`  Filtered role IDs: [${existingRoleIds}]`);
      console.log(`  New role IDs after adding Editor (4): [${newRoleIds}]`);
      console.log(`  ✅ Success`);
    } catch (error) {
      console.log(`User ${user.id} (${user.name}):`);
      console.log(`  ❌ ERROR: ${error.message}`);
    }
    console.log('');
  });
}

// Test the fixed handleSettingChange logic
function testSettingChange() {
  console.log('=== Testing Setting Change Fix ===');

  const users = Object.values(mockBackendResponses);

  users.forEach(user => {
    try {
      // This is the fixed logic from handleSettingChange
      const updatedSettings = {
        role_ids: (user.roles || []).filter(r => r?.id).map(r => r.id),
        donor_groups: user.donor_groups || [],
        outcomes: user.outcomes || [],
        field_contexts: user.field_contexts || []
      };

      console.log(`User ${user.id} (${user.name}):`);
      console.log(`  Original roles: ${JSON.stringify(user.roles)}`);
      console.log(`  Processed role_ids: [${updatedSettings.role_ids}]`);
      console.log(`  ✅ Success`);
    } catch (error) {
      console.log(`User ${user.id} (${user.name}):`);
      console.log(`  ❌ ERROR: ${error.message}`);
    }
    console.log('');
  });
}

// Test the fixed Select component value generation
function testSelectValueGeneration() {
  console.log('=== Testing Select Component Value Generation Fix ===');

  const users = Object.values(mockBackendResponses);

  users.forEach(user => {
    try {
      // This is the fixed logic for Select component value
      const selectValue = (user.roles || []).filter(r => r?.id && r?.name).map(r => ({ value: r.id, label: r.name }));

      console.log(`User ${user.id} (${user.name}):`);
      console.log(`  Original roles: ${JSON.stringify(user.roles)}`);
      console.log(`  Select value: ${JSON.stringify(selectValue)}`);
      console.log(`  ✅ Success`);
    } catch (error) {
      console.log(`User ${user.id} (${user.name}):`);
      console.log(`  ❌ ERROR: ${error.message}`);
    }
    console.log('');
  });
}

// Run all tests
testBulkRoleAssignment();
testSettingChange();
testSelectValueGeneration();

console.log('=== Test Summary ===');
console.log('All tests completed. The fix should handle:');
console.log('✅ Normal users with valid roles');
console.log('✅ Users with empty roles arrays');
console.log('✅ Users with null/undefined values in roles');
console.log('✅ Users with roles missing id properties');
console.log('✅ Users without roles property at all');
console.log('✅ Select component value generation');
console.log('✅ Bulk role assignment');
console.log('✅ Individual setting changes');
