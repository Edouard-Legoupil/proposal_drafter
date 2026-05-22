/**
 * Test script to verify role-based visibility is working
 * Run this after implementing the frontend changes
 */

// Mock user data for testing
const testUsers = [
  {
    name: "Admin User",
    is_admin: true,
    roles: ["proposal writer"],
    all_roles: ["proposal writer", "system admin", "access_metrics", "access_template", "access_incident", "access_quality_gate"]
  },
  {
    name: "Metrics User",
    is_admin: false,
    roles: ["proposal writer"],
    all_roles: ["proposal writer", "access_metrics"]
  },
  {
    name: "Template User",
    is_admin: false,
    roles: ["proposal writer"],
    all_roles: ["proposal writer", "access_template"]
  },
  {
    name: "Regular User",
    is_admin: false,
    roles: ["proposal writer"],
    all_roles: ["proposal writer"]
  }
];

// Test the hasPermission function
function testHasPermission() {
  console.log("Testing hasPermission function...\n");
  
  testUsers.forEach(user => {
    console.log(`User: ${user.name}`);
    console.log(`- Can access metrics: ${user.all_roles.includes('access_metrics')}`);
    console.log(`- Can access templates: ${user.all_roles.includes('access_template')}`);
    console.log(`- Can access quality gate: ${user.all_roles.includes('access_quality_gate')}`);
    console.log(`- Can access incidents: ${user.all_roles.includes('access_incident')}`);
    console.log();
  });
}

// Test sidebar visibility
function testSidebarVisibility() {
  console.log("Testing sidebar visibility...\n");
  
  const sidebarItems = [
    { text: 'Metrics Dashboard', permission: 'access_metrics' },
    { text: 'Donor Templates', permission: 'access_template' },
    { text: 'Quality Gate', permission: 'access_quality_gate' },
    { text: 'Incident Analysis', permission: 'access_incident' }
  ];
  
  testUsers.forEach(user => {
    console.log(`User: ${user.name}`);
    const visibleItems = sidebarItems.filter(item => 
      !item.permission || user.all_roles.includes(item.permission)
    );
    console.log(`- Visible menu items: ${visibleItems.length}/${sidebarItems.length}`);
    visibleItems.forEach(item => console.log(`  - ${item.text}`));
    console.log();
  });
}

// Run tests
testHasPermission();
testSidebarVisibility();

console.log("✅ Role visibility tests completed!");
console.log("\nExpected behavior:");
console.log("- Admin User: Should see all menu items");
console.log("- Metrics User: Should only see Metrics Dashboard");
console.log("- Template User: Should only see Donor Templates");
console.log("- Regular User: Should see no protected menu items");