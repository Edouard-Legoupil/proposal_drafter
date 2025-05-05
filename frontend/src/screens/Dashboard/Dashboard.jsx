import './Dashboard.css'

import { useEffect, useState } from 'react'

import Base from '../../components/Base/Base'
import CommonButton from '../../components/CommonButton/CommonButton'
import Project from './components/Project/Project'

import createNew from "../../assets/images/dashboard-createnew.svg"
import fileIcon from "../../assets/images/dashboard-fileIcon.svg"
import search from "../../assets/images/dashboard-search.svg"

export default function Dashboard ()
{
        const [projects, setProjects] = useState()
        useEffect(() => {
                setTimeout(() => {
                        setProjects([
                                {
                                        title: "Education for Refugees Initiative",
                                        date: "25 March 2025 - 10:00",
                                        status: "In Progress",
                                        content: "This initiative aims to establish educational programs for displaced children in refugee camps, providing access to primary education and vocational training."
                                },
                                {
                                        title: "Sustainable Agriculture Program",
                                        date: "22 March 2025 - 14:30",
                                        status: "Pending Approval",
                                        content: "A program focused on training local farmers in sustainable agriculture techniques to improve food security and economic stability in rural areas."
                                },
                                {
                                        title: "Healthcare Access Expansion",
                                        date: "20 March 2025 - 09:00",
                                        status: "Completed",
                                        content: "A collaborative effort with local health authorities to enhance primary healthcare services in underserved regions through mobile clinics and telemedicine."
                                },
                                {
                                        title: "Tech4Women Initiative",
                                        date: "18 March 2025 - 13:45",
                                        status: "In Progress",
                                        content: "A digital literacy and entrepreneurship program aimed at empowering women in developing communities through technology training."
                                },
                                {
                                        title: "Emergency Housing Relief",
                                        date: "16 March 2025 - 11:00",
                                        status: "In Progress",
                                        content: "A rapid response initiative to provide temporary housing and essential services to families displaced by natural disasters."
                                },
                                {
                                        title: "Renewable Energy for Rural Areas",
                                        date: "14 March 2025 - 16:00",
                                        status: "Pending Approval",
                                        content: "A project designed to install solar panels and microgrids in off-grid communities, ensuring access to clean and sustainable energy."
                                },
                                {
                                        title: "Digital Skills for Youth",
                                        date: "12 March 2025 - 10:15",
                                        status: "Completed",
                                        content: "A training initiative focused on equipping young people with coding, data analysis, and IT skills to enhance employment opportunities."
                                },
                                {
                                        title: "Water Sanitation & Hygiene (WASH)",
                                        date: "10 March 2025 - 14:45",
                                        status: "Completed",
                                        content: "An infrastructure development project focused on improving access to clean water and sanitation facilities in low-income communities."
                                },
                                {
                                        title: "Urban Green Spaces Initiative",
                                        date: "8 March 2025 - 12:30",
                                        status: "In Progress",
                                        content: "A collaborative project to develop public green spaces in densely populated urban areas to improve air quality and community well-being."
                                },
                                {
                                        title: "AI for Humanitarian Response",
                                        date: "6 March 2025 - 15:30",
                                        status: "Completed",
                                        content: "An AI-driven solution designed to analyze crisis data and optimize resource distribution during humanitarian emergencies."
                                },
                                {
                                        title: "Financial Inclusion for Small Businesses",
                                        date: "4 March 2025 - 09:45",
                                        status: "Pending Approval",
                                        content: "A microfinance and digital banking initiative aimed at supporting small business owners and entrepreneurs in underserved regions."
                                },
                                {
                                        title: "Climate Resilience Training",
                                        date: "2 March 2025 - 11:20",
                                        status: "Completed",
                                        content: "A capacity-building program focused on training communities in disaster preparedness and climate adaptation strategies."
                                }
                        ])
                }, 500)
        }, [])

        return  <Base>
                <div className="Dashboard">
                        <div className='Dashboard_top'>
                                <div className='Dashboard_label'>
                                        <img className='Dashboard_label_fileIcon' src={fileIcon} />
                                        Proposals
                                </div>
                                <CommonButton icon={createNew} label="Create New Proposal" onClick={() => window.location.href = "/chat"} />
                        </div>
                        {projects ?
                                <div className='Dashboard_search'>
                                        <img src={search} />
                                        <input type="text" className='Dashboard_search_input' placeholder='Search' />
                                </div>
                                :
                                ""
                        }
                        <div className='Dashboard_projects'>
                                {projects ? projects.map((project, i) =>
                                        <Project key={i} title={project.title} date={project.date} status={project.status}>
                                                {project.content}
                                        </Project>
                                ) : ""}
                        </div>
                </div>
        </Base>
}
