import './Project.css'

import { useNavigate } from 'react-router-dom'
import Markdown from 'react-markdown'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import tripleDots from "../../../../assets/images/dashboard-tripleDots.svg"
import calendar from "../../../../assets/images/dashboard-calendar.svg"
import view from "../../../../assets/images/login_showPassword.svg"
import bin from "../../../../assets/images/delete.svg"

export default function Project (props)
{
        const navigate = useNavigate()
        async function handleDeleteProject ()
        {
                const response  = await fetch(`${API_BASE_URL}/delete-draft/${props?.proposal_id}`, {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include'
                })

                if(response.ok)
                        navigate(0)
                else if(response.status === 401)
                {
                        sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                        navigate("/login")
                }
                else
                {
                        navigate(0)
                }
        }

        return  <div className='Dashboard_project' onClick={e => props?.onClick(e, props?.proposal_id)}>
                <div className='Dashboard_project_title'>
                        {props?.project_title}
                        <button className='Dashboard_project_tripleDotsContainer' popoverTarget={`popover-${props?.projectIndex+1}`} popoverTargetAction="toggle">
                                <img className='Dashboard_project_tripleDots' src={tripleDots} />
                        </button>
                </div>

                <div popover="auto" className='Project_optionsPopover' id={`popover-${props?.projectIndex+1}`} >
                        <div className='Project_optionsPopover_option'>
                                <img src={view} />
                                View
                        </div>

                        <div className='Project_optionsPopover_option' onClick={handleDeleteProject}>
                                <img className='Project_optionsPopover_option_delete' src={bin} />
                                Delete
                        </div>
                </div>

                <div className='Dashboard_project_description'>
                        <Markdown>
                                {props?.children}
                        </Markdown>
                        <div className='Dashboard_project_fade' />
                </div>

                <div className='Dashboard_project_footer'>
                        <div className='Dashboard_project_date'>
                                <img src={calendar} />
                                {props?.date}
                        </div>

                        <div
                                className='Dashboard_project_label'
                                style={{background: props?.status ? "#01A89A" : "#FF671F"}}
                        >
                                {props?.status ? "Approved" : "Pending approval"}
                        </div>
                </div>
        </div>
}
