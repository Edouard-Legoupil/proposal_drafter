SYSTEM_INHERITED_SETTING_IS_EFFECTIVE = """
(
    LOWER(TRIM(COALESCE(CAST(usr.approved_by AS TEXT), ''))) <> 'system'
    OR EXISTS (
        SELECT 1
        FROM team_members tm
        JOIN team_settings ts ON ts.team_id = tm.team_id
        WHERE tm.user_id = usr.user_id
          AND tm.status = 'ACTIVE'
          AND LOWER(TRIM(ts.setting_type)) = LOWER(TRIM(usr.setting_type))
          AND LOWER(TRIM(CAST(ts.setting_value AS TEXT))) =
              LOWER(TRIM(CAST(usr.setting_value AS TEXT)))
    )
)
"""
